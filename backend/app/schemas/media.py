from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class DownloadMode(str, Enum):
    VIDEO_AUDIO = "video_audio"
    AUDIO_ONLY = "audio_only"
    VIDEO_ONLY = "video_only"

class JobStatus(str, Enum):
    QUEUED = "queued"
    ANALYZING = "analyzing"
    DOWNLOADING = "downloading"
    MERGING = "merging"
    CONVERTING = "converting"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class QualityOption(BaseModel):
    format_id: str
    resolution: str  # e.g. "1080p", "720p", "480p", "360p"
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    container: str  # e.g. "mp4", "webm", "mkv"
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    filesize_bytes: Optional[int] = None
    estimated_mb: Optional[float] = None
    has_video: bool = True
    has_audio: bool = False
    requires_merging: bool = False
    is_available: bool = True
    is_recommended: bool = False
    status_label: str = "Ready"  # "Ready", "Requires merging", "Requires conversion", "Unavailable"

class AudioOption(BaseModel):
    format_id: str
    container: str  # e.g. "m4a", "mp3", "opus", "wav"
    acodec: Optional[str] = None
    abr_kbps: Optional[int] = None
    filesize_bytes: Optional[int] = None
    estimated_mb: Optional[float] = None
    quality_label: str  # e.g. "320 kbps (Ultra)", "192 kbps (High)", "128 kbps (Standard)"
    is_recommended: bool = False

class VideoMetadata(BaseModel):
    id: str
    url: str
    title: str
    description: Optional[str] = None
    channel: Optional[str] = None
    channel_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    duration_formatted: str = "0:00"
    thumbnail: Optional[str] = None
    source_provider: str  # "youtube", "vimeo", "archive.org", "mock"
    is_download_permitted: bool = True
    permission_notice: Optional[str] = None
    video_options: List[QualityOption] = Field(default_factory=list)
    audio_options: List[AudioOption] = Field(default_factory=list)
    best_compatible_video_format_id: Optional[str] = None
    best_compatible_audio_format_id: Optional[str] = None

class AnalyzeRequest(BaseModel):
    url: str

class AnalyzeResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    data: Optional[VideoMetadata] = None

class DownloadRequest(BaseModel):
    url: str
    mode: DownloadMode = DownloadMode.VIDEO_AUDIO
    resolution: Optional[str] = None  # e.g. "1080p", "720p", "best"
    format_id: Optional[str] = None
    target_container: str = "mp4"  # "mp4", "webm", "mkv", "mp3", "m4a", "wav"
    audio_format_id: Optional[str] = None
    audio_quality: Optional[str] = "best"

class JobProgress(BaseModel):
    job_id: str
    status: JobStatus
    stage_label: str = "Initializing"
    progress_percent: float = 0.0
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    download_speed_bytes: Optional[float] = None
    eta_seconds: Optional[int] = None
    error_message: Optional[str] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    created_at: str
    updated_at: str

class SearchRequest(BaseModel):
    query: str
    page: int = 1
    limit: int = 10

class SearchResultItem(BaseModel):
    id: str
    title: str
    channel: str
    duration_seconds: Optional[int] = None
    duration_formatted: str = "0:00"
    thumbnail: Optional[str] = None
    url: str
    source_provider: str = "youtube"
    published_at: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem] = Field(default_factory=list)
    total_count: int = 0
    has_more: bool = False
    is_provider_configured: bool = True
    provider_message: Optional[str] = None

class CapabilitiesResponse(BaseModel):
    app_name: str
    app_version: str = "1.0.0"
    ffmpeg_available: bool
    ffprobe_available: bool
    max_download_size_mb: int
    max_concurrent_jobs: int
    supported_video_containers: List[str] = ["mp4", "webm", "mkv"]
    supported_audio_containers: List[str] = ["mp3", "m4a", "opus", "wav"]
    supported_providers: List[str] = ["youtube", "vimeo", "dailymotion", "soundcloud", "archive.org"]
    search_configured: bool = False
