import asyncio
import os
import shutil
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any
from sqlalchemy import select, update, delete

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.models import DownloadJobModel
from backend.app.database.session import AsyncSessionLocal
from backend.app.media.processor import processor, MediaProcessingError
from backend.app.media.stream_selector import select_streams, StreamSelectionResult
from backend.app.providers.factory import get_provider_for_url
from backend.app.schemas.media import DownloadMode, JobStatus, JobProgress
from backend.app.security.validator import sanitize_filename, check_disk_space

class JobManager:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_JOBS)
        self.cancellation_tokens: Dict[str, bool] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        # In-memory progress cache for high-frequency progress polling
        self.progress_cache: Dict[str, Dict[str, Any]] = {}

    def is_cancelled(self, job_id: str) -> bool:
        return self.cancellation_tokens.get(job_id, False)

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        stage_label: str,
        progress_percent: float = 0.0,
        downloaded_bytes: Optional[int] = None,
        total_bytes: Optional[int] = None,
        download_speed_bytes: Optional[float] = None,
        eta_seconds: Optional[int] = None,
        error_message: Optional[str] = None,
        output_filename: Optional[str] = None,
        output_filepath: Optional[str] = None,
        output_filesize_bytes: Optional[int] = None
    ):
        now_str = datetime.now(timezone.utc).isoformat()
        self.progress_cache[job_id] = {
            "status": status,
            "stage_label": stage_label,
            "progress_percent": progress_percent,
            "downloaded_bytes": downloaded_bytes,
            "total_bytes": total_bytes,
            "download_speed_bytes": download_speed_bytes,
            "eta_seconds": eta_seconds,
            "error_message": error_message,
            "output_filename": output_filename,
            "output_filepath": output_filepath,
            "output_filesize_bytes": output_filesize_bytes,
            "updated_at": now_str
        }

        # Persist major milestone updates to DB
        async with AsyncSessionLocal() as session:
            stmt = (
                update(DownloadJobModel)
                .where(DownloadJobModel.id == job_id)
                .values(
                    status=status.value,
                    stage_label=stage_label,
                    progress_percent=progress_percent,
                    downloaded_bytes=downloaded_bytes or 0,
                    total_bytes=total_bytes or 0,
                    download_speed_bytes=download_speed_bytes or 0.0,
                    eta_seconds=eta_seconds,
                    error_message=error_message,
                    output_filename=output_filename,
                    output_filepath=output_filepath,
                    output_filesize_bytes=output_filesize_bytes,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def get_job_progress(self, job_id: str) -> Optional[JobProgress]:
        # First check cache
        cached = self.progress_cache.get(job_id)
        if cached:
            return JobProgress(
                job_id=job_id,
                status=cached["status"],
                stage_label=cached["stage_label"],
                progress_percent=cached["progress_percent"],
                downloaded_bytes=cached.get("downloaded_bytes"),
                total_bytes=cached.get("total_bytes"),
                download_speed_bytes=cached.get("download_speed_bytes"),
                eta_seconds=cached.get("eta_seconds"),
                error_message=cached.get("error_message"),
                file_name=cached.get("output_filename"),
                file_size_bytes=cached.get("output_filesize_bytes"),
                download_url=f"/api/downloads/{job_id}/file" if cached["status"] == JobStatus.COMPLETED else None,
                created_at=cached.get("updated_at", datetime.now(timezone.utc).isoformat()),
                updated_at=cached.get("updated_at", datetime.now(timezone.utc).isoformat())
            )

        # Fallback to database
        async with AsyncSessionLocal() as session:
            stmt = select(DownloadJobModel).where(DownloadJobModel.id == job_id)
            res = await session.execute(stmt)
            job = res.scalar_one_or_none()
            if not job:
                return None

            return JobProgress(
                job_id=job.id,
                status=JobStatus(job.status),
                stage_label=job.stage_label,
                progress_percent=job.progress_percent,
                downloaded_bytes=job.downloaded_bytes,
                total_bytes=job.total_bytes,
                download_speed_bytes=job.download_speed_bytes,
                eta_seconds=job.eta_seconds,
                error_message=job.error_message,
                file_name=job.output_filename,
                file_size_bytes=job.output_filesize_bytes,
                download_url=f"/api/downloads/{job.id}/file" if job.status == JobStatus.COMPLETED.value else None,
                created_at=job.created_at.isoformat() if job.created_at else datetime.now(timezone.utc).isoformat(),
                updated_at=job.updated_at.isoformat() if job.updated_at else datetime.now(timezone.utc).isoformat()
            )

    async def cancel_job(self, job_id: str) -> bool:
        self.cancellation_tokens[job_id] = True
        task = self.active_tasks.get(job_id)
        if task and not task.done():
            task.cancel()

        await self.update_job_status(
            job_id=job_id,
            status=JobStatus.CANCELLED,
            stage_label="Cancelled by user"
        )

        # Clean temp directory
        job_temp_dir = os.path.join(settings.TEMP_DIR, job_id)
        if os.path.exists(job_temp_dir):
            shutil.rmtree(job_temp_dir, ignore_errors=True)

        return True

    async def start_job(
        self,
        job_id: str,
        url: str,
        mode: DownloadMode,
        resolution: Optional[str] = None,
        format_id: Optional[str] = None,
        target_container: str = "mp4",
        audio_format_id: Optional[str] = None,
        audio_quality: Optional[str] = "best"
    ):
        task = asyncio.create_task(
            self._execute_job_pipeline(
                job_id=job_id,
                url=url,
                mode=mode,
                resolution=resolution,
                format_id=format_id,
                target_container=target_container,
                audio_format_id=audio_format_id,
                audio_quality=audio_quality
            )
        )
        self.active_tasks[job_id] = task

    async def _execute_job_pipeline(
        self,
        job_id: str,
        url: str,
        mode: DownloadMode,
        resolution: Optional[str],
        format_id: Optional[str],
        target_container: str,
        audio_format_id: Optional[str],
        audio_quality: Optional[str]
    ):
        job_temp_dir = os.path.join(settings.TEMP_DIR, job_id)
        os.makedirs(job_temp_dir, exist_ok=True)
        os.makedirs(settings.DOWNLOADS_DIR, exist_ok=True)

        try:
            # Check disk space
            if not check_disk_space(settings.TEMP_DIR, required_mb=500):
                raise MediaProcessingError("Insufficient server disk space to process this download.")

            async with self.semaphore:
                if self.is_cancelled(job_id):
                    return

                # Stage 1: Analyzing
                await self.update_job_status(job_id, JobStatus.ANALYZING, "Analyzing video and streams", 5.0)
                provider = get_provider_for_url(url)
                metadata = await provider.analyze(url)

                if not metadata.is_download_permitted:
                    raise MediaProcessingError(
                        metadata.permission_notice or "Download not permitted for this video."
                    )

                # Persist metadata to database job record
                async with AsyncSessionLocal() as session:
                    stmt = (
                        update(DownloadJobModel)
                        .where(DownloadJobModel.id == job_id)
                        .values(
                            video_title=metadata.title,
                            channel=metadata.channel,
                            thumbnail=metadata.thumbnail,
                            duration_seconds=metadata.duration_seconds
                        )
                    )
                    await session.execute(stmt)
                    await session.commit()

                if self.is_cancelled(job_id):
                    return

                # Stage 2: Stream Selection
                selection: StreamSelectionResult = select_streams(
                    metadata=metadata,
                    mode=mode,
                    requested_resolution=resolution,
                    requested_format_id=format_id,
                    target_container=target_container,
                    requested_audio_quality=audio_quality or "best"
                )

                safe_title = sanitize_filename(metadata.title)
                final_filename = f"{safe_title}_{resolution or 'best'}_{job_id[:8]}.{target_container}"
                final_output_path = os.path.join(settings.DOWNLOADS_DIR, final_filename)

                # Progress hook callback for yt-dlp
                def yt_progress_hook(d):
                    if self.is_cancelled(job_id):
                        raise asyncio.CancelledError()
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
                    downloaded = d.get("downloaded_bytes", 0)
                    pct = min(90.0, (downloaded / total) * 80.0 + 10.0) if total > 0 else 25.0
                    speed = d.get("speed")
                    eta = d.get("eta")

                    # Update cache without hammering DB every block
                    self.progress_cache[job_id] = {
                        "status": JobStatus.DOWNLOADING,
                        "stage_label": f"Downloading stream ({int(pct)}%)",
                        "progress_percent": round(pct, 1),
                        "downloaded_bytes": downloaded,
                        "total_bytes": total,
                        "download_speed_bytes": speed,
                        "eta_seconds": eta,
                        "error_message": None,
                        "output_filename": None,
                        "output_filepath": None,
                        "output_filesize_bytes": None,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }

                # Stage 3: Download
                await self.update_job_status(job_id, JobStatus.DOWNLOADING, "Downloading media stream(s)", 15.0)

                if selection.requires_merging:
                    # Download separate video and audio streams concurrently for super-fast acquisition
                    video_tmpl = os.path.join(job_temp_dir, f"video_stream.%(ext)s")
                    audio_tmpl = os.path.join(job_temp_dir, f"audio_stream.%(ext)s")

                    stream_stats = {
                        "video_bytes": 0,
                        "video_total": 0,
                        "audio_bytes": 0,
                        "audio_total": 0,
                        "video_speed": 0,
                        "audio_speed": 0,
                    }

                    def make_concurrent_hook(stream_type: str):
                        def _hook(d):
                            if self.is_cancelled(job_id):
                                raise asyncio.CancelledError()
                            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                            downloaded = d.get("downloaded_bytes", 0)
                            stream_stats[f"{stream_type}_bytes"] = downloaded
                            if total > 0:
                                stream_stats[f"{stream_type}_total"] = total
                            speed = d.get("speed") or 0
                            stream_stats[f"{stream_type}_speed"] = speed

                            combined_downloaded = stream_stats["video_bytes"] + stream_stats["audio_bytes"]
                            combined_total = stream_stats["video_total"] + stream_stats["audio_total"]
                            combined_speed = stream_stats["video_speed"] + stream_stats["audio_speed"]

                            if combined_total > 0:
                                pct = min(90.0, (combined_downloaded / combined_total) * 80.0 + 10.0)
                            else:
                                pct = 25.0

                            eta = d.get("eta")

                            self.progress_cache[job_id] = {
                                "status": JobStatus.DOWNLOADING,
                                "stage_label": f"Downloading streams concurrently ({int(pct)}%)",
                                "progress_percent": round(pct, 1),
                                "downloaded_bytes": combined_downloaded,
                                "total_bytes": combined_total,
                                "download_speed_bytes": combined_speed if combined_speed > 0 else None,
                                "eta_seconds": eta,
                                "error_message": None,
                                "output_filename": None,
                                "output_filepath": None,
                                "output_filesize_bytes": None,
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }
                        return _hook

                    video_task = provider.download_stream(
                        url=url,
                        format_id=selection.video_format_id,
                        output_template=video_tmpl,
                        progress_callback=make_concurrent_hook("video"),
                        cancel_check=lambda: self.is_cancelled(job_id)
                    )
                    audio_task = provider.download_stream(
                        url=url,
                        format_id=selection.audio_format_id,
                        output_template=audio_tmpl,
                        progress_callback=make_concurrent_hook("audio"),
                        cancel_check=lambda: self.is_cancelled(job_id)
                    )

                    await asyncio.gather(video_task, audio_task)

                    if self.is_cancelled(job_id):
                        return

                    # Locate actual downloaded files in temp
                    video_file = None
                    audio_file = None
                    for fname in os.listdir(job_temp_dir):
                        if fname.startswith("video_stream"):
                            video_file = os.path.join(job_temp_dir, fname)
                        elif fname.startswith("audio_stream"):
                            audio_file = os.path.join(job_temp_dir, fname)

                    if not video_file or not audio_file:
                        raise MediaProcessingError("Failed to locate downloaded video/audio stream files.")

                    # Stage 4: Merging
                    await self.update_job_status(job_id, JobStatus.MERGING, "Combining audio and video streams", 85.0)
                    stream_copy = not selection.requires_conversion

                    await processor.merge_streams(
                        video_path=video_file,
                        audio_path=audio_file,
                        output_path=final_output_path,
                        stream_copy=stream_copy,
                        target_container=target_container
                    )

                else:
                    # Single stream download (combined video or audio-only)
                    stream_format_id = selection.video_format_id or selection.audio_format_id
                    single_tmpl = os.path.join(job_temp_dir, f"stream.%(ext)s")

                    await provider.download_stream(
                        url=url,
                        format_id=stream_format_id,
                        output_template=single_tmpl,
                        progress_callback=yt_progress_hook,
                        cancel_check=lambda: self.is_cancelled(job_id)
                    )

                    if self.is_cancelled(job_id):
                        return

                    single_file = None
                    for fname in os.listdir(job_temp_dir):
                        if fname.startswith("stream."):
                            single_file = os.path.join(job_temp_dir, fname)
                            break

                    if not single_file:
                        raise MediaProcessingError("Downloaded stream file not found.")

                    if selection.requires_conversion:
                        stage_name = f"Converting to {target_container.upper()}"
                        await self.update_job_status(job_id, JobStatus.CONVERTING, stage_name, 85.0)
                        await processor.convert_or_extract(
                            input_path=single_file,
                            output_path=final_output_path,
                            is_audio_only=(mode == DownloadMode.AUDIO_ONLY),
                            target_container=target_container
                        )
                    else:
                        # Direct move to downloads
                        shutil.move(single_file, final_output_path)

                if self.is_cancelled(job_id):
                    return

                # Stage 5: Validating
                await self.update_job_status(job_id, JobStatus.VALIDATING, "Validating final media file", 95.0)
                await processor.validate_output(
                    final_output_path,
                    require_video=(mode != DownloadMode.AUDIO_ONLY),
                    require_audio=(mode != DownloadMode.VIDEO_ONLY)
                )

                final_size = os.path.getsize(final_output_path)

                # Stage 6: Completed
                await self.update_job_status(
                    job_id=job_id,
                    status=JobStatus.COMPLETED,
                    stage_label="Completed",
                    progress_percent=100.0,
                    downloaded_bytes=final_size,
                    total_bytes=final_size,
                    output_filename=final_filename,
                    output_filepath=final_output_path,
                    output_filesize_bytes=final_size
                )
                logger.info(f"Job {job_id} successfully completed. Output: {final_output_path} ({final_size} bytes)")

        except asyncio.CancelledError:
            logger.info(f"Job {job_id} cancelled.")
            await self.update_job_status(job_id, JobStatus.CANCELLED, "Cancelled by user")
            if os.path.exists(final_output_path):
                os.remove(final_output_path)
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            await self.update_job_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                stage_label="Failed",
                error_message=str(e)
            )
        finally:
            # Clean up job temp directory
            shutil.rmtree(job_temp_dir, ignore_errors=True)
            self.active_tasks.pop(job_id, None)

    async def cleanup_expired_jobs(self):
        """
        Removes files and marks jobs expired according to retention policy.
        """
        threshold = datetime.now(timezone.utc) - timedelta(hours=settings.JOB_RETENTION_HOURS)
        async with AsyncSessionLocal() as session:
            stmt = select(DownloadJobModel).where(
                DownloadJobModel.created_at < threshold,
                DownloadJobModel.is_expired == False
            )
            res = await session.execute(stmt)
            expired_jobs = res.scalars().all()

            for job in expired_jobs:
                if job.output_filepath and os.path.exists(job.output_filepath):
                    try:
                        os.remove(job.output_filepath)
                        logger.info(f"Cleaned up expired media file: {job.output_filepath}")
                    except Exception as e:
                        logger.warning(f"Error removing expired file {job.output_filepath}: {e}")
                job.is_expired = True

            await session.commit()

job_manager = JobManager()
