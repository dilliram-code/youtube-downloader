import asyncio
import os
import shutil
from typing import Optional, Callable
from backend.app.schemas.media import (
    VideoMetadata,
    QualityOption,
    AudioOption,
    SearchResponse,
    SearchResultItem
)
from backend.app.providers.base import BaseMediaProvider

class MockMediaProvider(BaseMediaProvider):
    def __init__(self, fixture_video_path: Optional[str] = None, fixture_audio_path: Optional[str] = None):
        self.fixture_video_path = fixture_video_path
        self.fixture_audio_path = fixture_audio_path

    async def analyze(self, url: str) -> VideoMetadata:
        if "unauthorized" in url:
            return VideoMetadata(
                id="unauth123",
                url=url,
                title="Restricted / Private Media",
                channel="Private Channel",
                thumbnail="",
                source_provider="mock",
                is_download_permitted=False,
                permission_notice="This content is protected by access controls or private-video restrictions and direct download is not permitted."
            )

        video_opts = [
            QualityOption(
                format_id="mock_2160p",
                resolution="2160p",
                width=3840,
                height=2160,
                fps=60.0,
                container="mp4",
                vcodec="av01.0.12M.08",
                filesize_bytes=240_000_000,
                estimated_mb=228.9,
                has_video=True,
                has_audio=False,
                requires_merging=True,
                status_label="Requires merging"
            ),
            QualityOption(
                format_id="mock_1080p",
                resolution="1080p",
                width=1920,
                height=1080,
                fps=30.0,
                container="mp4",
                vcodec="avc1.640028",
                filesize_bytes=85_000_000,
                estimated_mb=81.1,
                has_video=True,
                has_audio=False,
                requires_merging=True,
                is_recommended=True,
                status_label="Requires merging"
            ),
            QualityOption(
                format_id="mock_720p",
                resolution="720p",
                width=1280,
                height=720,
                fps=30.0,
                container="mp4",
                vcodec="avc1.4d401f",
                filesize_bytes=42_000_000,
                estimated_mb=40.0,
                has_video=True,
                has_audio=True,
                acodec="mp4a.40.2",
                requires_merging=False,
                status_label="Ready"
            ),
            QualityOption(
                format_id="mock_480p",
                resolution="480p",
                width=854,
                height=480,
                fps=30.0,
                container="mp4",
                vcodec="avc1.4d401e",
                filesize_bytes=20_000_000,
                estimated_mb=19.1,
                has_video=True,
                has_audio=True,
                acodec="mp4a.40.2",
                requires_merging=False,
                status_label="Ready"
            )
        ]

        audio_opts = [
            AudioOption(
                format_id="mock_a256",
                container="m4a",
                acodec="mp4a.40.2",
                abr_kbps=256,
                filesize_bytes=12_000_000,
                estimated_mb=11.4,
                quality_label="256 kbps (Ultra)",
                is_recommended=True
            ),
            AudioOption(
                format_id="mock_a128",
                container="m4a",
                acodec="mp4a.40.2",
                abr_kbps=128,
                filesize_bytes=6_000_000,
                estimated_mb=5.7,
                quality_label="128 kbps (Standard)"
            )
        ]

        return VideoMetadata(
            id="mock_test_video",
            url=url,
            title="Vidora Sample Showcase Video",
            description="A sample test video for testing media workflows.",
            channel="Vidora Media Labs",
            channel_url="https://test-media.local/channel",
            duration_seconds=185,
            duration_formatted="3:05",
            thumbnail="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&q=80",
            source_provider="mock",
            is_download_permitted=True,
            video_options=video_opts,
            audio_options=audio_opts,
            best_compatible_video_format_id="mock_1080p",
            best_compatible_audio_format_id="mock_a256"
        )

    async def search(self, query: str, page: int = 1, limit: int = 10) -> SearchResponse:
        results = [
            SearchResultItem(
                id="mock_item_1",
                title=f"Sample Search Result for {query}",
                channel="Creative Labs",
                duration_seconds=240,
                duration_formatted="4:00",
                thumbnail="https://images.unsplash.com/photo-1536240478700-b869070f9279?w=600&q=80",
                url="https://test-media.local/watch?v=mock_item_1",
                source_provider="mock",
                published_at="2026-01-15T12:00:00Z"
            ),
            SearchResultItem(
                id="mock_item_2",
                title=f"Exploring Modern Soundscapes - {query}",
                channel="Sound Studio",
                duration_seconds=192,
                duration_formatted="3:12",
                thumbnail="https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&q=80",
                url="https://test-media.local/watch?v=mock_item_2",
                source_provider="mock",
                published_at="2026-02-01T08:30:00Z"
            )
        ]
        return SearchResponse(
            query=query,
            results=results,
            total_count=len(results),
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
        # Simulate download progress
        for pct in (25, 50, 75, 100):
            if cancel_check and cancel_check():
                raise asyncio.CancelledError("Download cancelled")
            if progress_callback:
                progress_callback({
                    "status": "downloading",
                    "downloaded_bytes": pct * 100_000,
                    "total_bytes": 10_000_000,
                    "speed": 1_500_000,
                    "eta": (100 - pct) // 25
                })
            await asyncio.sleep(0.05)

        # Copy fixture if available, otherwise generate tiny test video/audio via ffmpeg
        dest = output_template.replace("%(ext)s", "mp4")
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        if "audio" in format_id or "mock_a" in format_id:
            if self.fixture_audio_path and os.path.exists(self.fixture_audio_path):
                shutil.copyfile(self.fixture_audio_path, dest)
            else:
                # Generate 1-second synthetic silent audio file with ffmpeg
                proc = await asyncio.create_subprocess_exec(
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    "-t", "1", "-c:a", "aac", dest,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
        else:
            if self.fixture_video_path and os.path.exists(self.fixture_video_path):
                shutil.copyfile(self.fixture_video_path, dest)
            else:
                # Generate 1-second synthetic test video with ffmpeg
                proc = await asyncio.create_subprocess_exec(
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=30",
                    "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p", dest,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()

        return dest
