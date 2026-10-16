import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.models import DownloadJobModel
from backend.app.database.session import get_db
from backend.app.jobs.manager import job_manager
from backend.app.providers.factory import get_provider_for_url, get_default_provider
from backend.app.schemas.media import (
    AnalyzeRequest,
    AnalyzeResponse,
    CapabilitiesResponse,
    DownloadRequest,
    JobProgress,
    JobStatus,
    SearchResponse
)
from backend.app.security.validator import validate_video_url

router = APIRouter(prefix="/api", tags=["Media"])

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV
    }

@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities():
    ffmpeg_ok = bool(shutil.which(settings.FFMPEG_PATH) or os.path.exists(settings.FFMPEG_PATH))
    ffprobe_ok = bool(shutil.which(settings.FFPROBE_PATH) or os.path.exists(settings.FFPROBE_PATH))

    return CapabilitiesResponse(
        app_name=settings.APP_NAME,
        ffmpeg_available=ffmpeg_ok,
        ffprobe_available=ffprobe_ok,
        max_download_size_mb=settings.MAX_DOWNLOAD_SIZE_MB,
        max_concurrent_jobs=settings.MAX_CONCURRENT_JOBS,
        search_configured=bool(settings.YOUTUBE_API_KEY)
    )

@router.post("/video/analyze", response_model=AnalyzeResponse)
async def analyze_video(payload: AnalyzeRequest):
    valid, normalized_url, detected_provider = validate_video_url(payload.url)
    if not valid:
        return AnalyzeResponse(success=False, error=normalized_url, data=None)

    try:
        provider = get_provider_for_url(normalized_url)
        metadata = await provider.analyze(normalized_url)
        return AnalyzeResponse(success=True, data=metadata)
    except Exception as e:
        logger.error(f"Analysis error for {payload.url}: {e}")
        return AnalyzeResponse(success=False, error=str(e), data=None)

@router.get("/video/search", response_model=SearchResponse)
async def search_videos(
    q: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50)
):
    provider = get_default_provider()
    try:
        return await provider.search(query=q, page=page, limit=limit)
    except Exception as e:
        logger.error(f"Search endpoint error for query '{q}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search service error: {str(e)}"
        )

@router.post("/downloads", response_model=JobProgress, status_code=status.HTTP_202_ACCEPTED)
async def create_download_job(
    payload: DownloadRequest,
    db: AsyncSession = Depends(get_db)
):
    valid, normalized_url, detected_provider = validate_video_url(payload.url)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=normalized_url
        )

    job_id = f"job_{uuid.uuid4().hex[:16]}"

    # Insert job into database
    new_job = DownloadJobModel(
        id=job_id,
        url=normalized_url,
        mode=payload.mode.value,
        resolution=payload.resolution,
        target_container=payload.target_container,
        format_id=payload.format_id,
        audio_format_id=payload.audio_format_id,
        status=JobStatus.QUEUED.value,
        stage_label="Queued"
    )
    db.add(new_job)
    await db.commit()

    # Trigger background worker
    await job_manager.start_job(
        job_id=job_id,
        url=normalized_url,
        mode=payload.mode,
        resolution=payload.resolution,
        format_id=payload.format_id,
        target_container=payload.target_container,
        audio_format_id=payload.audio_format_id,
        audio_quality=payload.audio_quality
    )

    progress = await job_manager.get_job_progress(job_id)
    if not progress:
        raise HTTPException(status_code=500, detail="Failed to initialize job progress tracker.")
    return progress

@router.get("/downloads/{job_id}", response_model=JobProgress)
async def get_job_status(job_id: str):
    progress = await job_manager.get_job_progress(job_id)
    if not progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download job not found.")
    return progress

@router.get("/downloads/{job_id}/file")
async def get_downloaded_file(job_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(DownloadJobModel).where(DownloadJobModel.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job record not found.")

    if job.status != JobStatus.COMPLETED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Media file is not ready yet.")

    if job.is_expired or not job.output_filepath or not os.path.exists(job.output_filepath):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="The generated media file has expired or was removed.")

    # Prevent directory traversal
    resolved_file = os.path.realpath(job.output_filepath)
    resolved_storage = os.path.realpath(settings.DOWNLOADS_DIR)
    if not resolved_file.startswith(resolved_storage):
        logger.error(f"Potential directory traversal attempt on job {job_id}: {resolved_file}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    media_type = "video/mp4" if job.target_container == "mp4" else (
        "audio/mpeg" if job.target_container == "mp3" else (
            "audio/mp4" if job.target_container == "m4a" else (
                "video/webm" if job.target_container == "webm" else "application/octet-stream"
            )
        )
    )

    return FileResponse(
        path=resolved_file,
        filename=job.output_filename or f"download.{job.target_container}",
        media_type=media_type,
        content_disposition_type="attachment"
    )

@router.delete("/downloads/{job_id}")
async def cancel_or_delete_job(job_id: str, db: AsyncSession = Depends(get_db)):
    progress = await job_manager.get_job_progress(job_id)
    if not progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    if progress.status in (JobStatus.QUEUED, JobStatus.ANALYZING, JobStatus.DOWNLOADING, JobStatus.MERGING, JobStatus.CONVERTING):
        await job_manager.cancel_job(job_id)
        return {"success": True, "message": "Job cancelled successfully."}

    # If completed or failed, remove record and file
    stmt = select(DownloadJobModel).where(DownloadJobModel.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if job:
        if job.output_filepath and os.path.exists(job.output_filepath):
            try:
                os.remove(job.output_filepath)
            except Exception:
                pass
        await db.delete(job)
        await db.commit()

    return {"success": True, "message": "Job and artifacts removed."}

@router.get("/history", response_model=List[JobProgress])
async def list_download_history(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(DownloadJobModel)
        .order_by(desc(DownloadJobModel.created_at))
        .limit(limit)
    )
    res = await db.execute(stmt)
    jobs = res.scalars().all()

    history = []
    for job in jobs:
        history.append(JobProgress(
            job_id=job.id,
            status=JobStatus(job.status),
            stage_label=job.stage_label,
            progress_percent=job.progress_percent,
            downloaded_bytes=job.downloaded_bytes,
            total_bytes=job.total_bytes,
            download_speed_bytes=job.download_speed_bytes,
            eta_seconds=job.eta_seconds,
            error_message=job.error_message,
            file_name=job.output_filename or job.video_title,
            file_size_bytes=job.output_filesize_bytes,
            download_url=f"/api/downloads/{job.id}/file" if job.status == JobStatus.COMPLETED.value and not job.is_expired else None,
            created_at=job.created_at.isoformat() if job.created_at else "",
            updated_at=job.updated_at.isoformat() if job.updated_at else ""
        ))
    return history
