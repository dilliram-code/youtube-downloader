import asyncio
import os
import shutil
from typing import Dict, Any, List, Optional, Callable
import yt_dlp

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.media import (
    VideoMetadata,
    QualityOption,
    AudioOption,
    SearchResponse,
    SearchResultItem
)
from backend.app.providers.base import BaseMediaProvider

def format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "0:00"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

class YtDlpProvider(BaseMediaProvider):
    def __init__(self):
        self.default_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
            "noplaylist": True,
            "allow_unplayable_formats": False,
            "socket_timeout": 15,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "ios", "web"],
                    "player_skip": ["webpage", "configs"],
                }
            },
            "http_chunk_size": 10485760,
        }

    async def analyze(self, url: str) -> VideoMetadata:
        """
        Extracts real stream metadata without downloading video data.
        """
        def _extract():
            with yt_dlp.YoutubeDL(self.default_opts) as ydl:
                return ydl.extract_info(url, download=False)

        loop = asyncio.get_running_loop()
        try:
            info = await loop.run_in_executor(None, _extract)
        except Exception as e:
            logger.error(f"yt-dlp extraction error for {url}: {e}")
            raise ValueError(f"Failed to extract media information: {str(e)}")

        if not info:
            raise ValueError("No metadata returned by extractor.")

        formats = info.get("formats", [])
        video_options: Dict[str, QualityOption] = {}
        audio_options: Dict[str, AudioOption] = {}

        # Parse streams
        for f in formats:
            f_id = str(f.get("format_id", ""))
            vcodec = f.get("vcodec") or "none"
            acodec = f.get("acodec") or "none"
            ext = (f.get("ext") or "").lower()
            height = f.get("height")
            width = f.get("width")
            fps = f.get("fps")
            filesize = f.get("filesize") or f.get("filesize_approx")

            has_video = vcodec != "none"
            has_audio = acodec != "none"

            # Parse video stream
            if has_video and height:
                res_label = f"{height}p"
                # If we haven't seen this resolution, or this one is an MP4 / has higher bitrate
                existing = video_options.get(res_label)
                est_mb = round(filesize / (1024 * 1024), 1) if filesize else None
                status_lbl = "Ready" if has_audio else "Requires merging"

                option = QualityOption(
                    format_id=f_id,
                    resolution=res_label,
                    width=width,
                    height=height,
                    fps=fps,
                    container=ext,
                    vcodec=vcodec,
                    acodec=acodec if has_audio else None,
                    filesize_bytes=filesize,
                    estimated_mb=est_mb,
                    has_video=True,
                    has_audio=has_audio,
                    requires_merging=not has_audio,
                    is_available=True,
                    status_label=status_lbl
                )

                if not existing or (ext == "mp4" and existing.container != "mp4"):
                    video_options[res_label] = option

            # Parse audio stream
            if not has_video and has_audio:
                abr = f.get("abr") or (f.get("tbr") if not has_video else None)
                abr_int = int(abr) if abr else 128
                quality_lbl = f"{abr_int} kbps"
                if abr_int >= 256:
                    quality_lbl += " (Ultra)"
                elif abr_int >= 192:
                    quality_lbl += " (High)"
                elif abr_int >= 128:
                    quality_lbl += " (Standard)"
                else:
                    quality_lbl += " (Economy)"

                est_mb = round(filesize / (1024 * 1024), 1) if filesize else None
                audio_opt = AudioOption(
                    format_id=f_id,
                    container=ext,
                    acodec=acodec,
                    abr_kbps=abr_int,
                    filesize_bytes=filesize,
                    estimated_mb=est_mb,
                    quality_label=quality_lbl
                )
                audio_options[f_id] = audio_opt

        # Sort video options by resolution (height) descending
        sorted_videos = sorted(
            video_options.values(),
            key=lambda x: x.height or 0,
            reverse=True
        )

        # Mark 1080p or highest <= 1080p as recommended default
        if sorted_videos:
            rec_found = False
            for v in sorted_videos:
                if (v.height or 0) == 1080:
                    v.is_recommended = True
                    rec_found = True
                    break
            if not rec_found and sorted_videos:
                sorted_videos[0].is_recommended = True

        # Sort audio options by bitrate descending
        sorted_audios = sorted(
            audio_options.values(),
            key=lambda a: a.abr_kbps or 0,
            reverse=True
        )
        if sorted_audios:
            sorted_audios[0].is_recommended = True

        duration = info.get("duration")

        return VideoMetadata(
            id=str(info.get("id", "")),
            url=url,
            title=info.get("title") or "Untitled Media",
            description=info.get("description") or "",
            channel=info.get("uploader") or info.get("channel") or "Unknown Channel",
            channel_url=info.get("uploader_url") or info.get("channel_url"),
            duration_seconds=duration,
            duration_formatted=format_duration(duration),
            thumbnail=info.get("thumbnail"),
            source_provider=info.get("extractor_key", "generic").lower(),
            is_download_permitted=True,
            video_options=sorted_videos,
            audio_options=sorted_audios,
            best_compatible_video_format_id=sorted_videos[0].format_id if sorted_videos else None,
            best_compatible_audio_format_id=sorted_audios[0].format_id if sorted_audios else None
        )

    async def search(self, query: str, page: int = 1, limit: int = 10) -> SearchResponse:
        """
        Uses authorized search provider. If YouTube API Key is configured, queries YouTube Data API.
        Otherwise provides a clear setup notice as required by Section 5.
        """
        if not settings.YOUTUBE_API_KEY:
            return SearchResponse(
                query=query,
                results=[],
                total_count=0,
                has_more=False,
                is_provider_configured=False,
                provider_message="Search provider is not configured. Add YOUTUBE_API_KEY to your environment variables to enable video search, or paste video URLs directly in the input field above."
            )

        # Official YouTube Data API v3 search
        import httpx
        params = {
            "part": "snippet",
            "q": query,
            "maxResults": limit,
            "type": "video",
            "key": settings.YOUTUBE_API_KEY
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://www.googleapis.com/youtube/v3/search", params=params)
            if resp.status_code != 200:
                logger.error(f"YouTube Search API error: {resp.text}")
                return SearchResponse(
                    query=query,
                    results=[],
                    total_count=0,
                    has_more=False,
                    is_provider_configured=True,
                    provider_message=f"YouTube Search API returned an error: {resp.status_code}"
                )
            data = resp.json()

        items = []
        for item in data.get("items", []):
            vid_id = item.get("id", {}).get("videoId")
            snippet = item.get("snippet", {})
            if vid_id:
                items.append(SearchResultItem(
                    id=vid_id,
                    title=snippet.get("title", ""),
                    channel=snippet.get("channelTitle", ""),
                    thumbnail=snippet.get("thumbnails", {}).get("high", {}).get("url"),
                    url=f"https://www.youtube.com/watch?v={vid_id}",
                    source_provider="youtube",
                    published_at=snippet.get("publishedAt")
                ))

        return SearchResponse(
            query=query,
            results=items,
            total_count=len(items),
            has_more=False,
            is_provider_configured=True
        )

    async def download_stream(
        self,
        url: str,
        format_id: str,
        output_template: str,
        progress_callback: Optional[Callable[[dict], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> str:
        """
        Downloads a specific stream using yt-dlp with progress hooks and cancellation support.
        """
        def _hook(d):
            if cancel_check and cancel_check():
                raise asyncio.CancelledError("Job was cancelled by user")
            if progress_callback and d.get("status") == "downloading":
                progress_callback(d)

        aria2c_exe = shutil.which("aria2c")
        ydl_opts: Dict[str, Any] = {
            "format": format_id,
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [_hook],
            "nocheckcertificate": False,
            "socket_timeout": 30,
            "retries": 10,
            "fragment_retries": 10,
            "file_access_retries": 5,
            "buffersize": 1048576,  # 1 MB buffer
            "http_chunk_size": 10485760,  # 10 MB HTTP chunks to avoid throttle
            "concurrent_fragment_downloads": 16,  # 16 parallel fragment streams
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "ios", "web"],
                }
            },
        }

        if aria2c_exe:
            ydl_opts["external_downloader"] = {"default": "aria2c"}
            ydl_opts["external_downloader_args"] = {
                "aria2c": [
                    "-c",
                    "-j", "16",
                    "-x", "16",
                    "-s", "16",
                    "-k", "1M",
                    "--min-split-size=1M",
                    "--summary-interval=0"
                ]
            }

        def _run():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _run)
        return output_template
