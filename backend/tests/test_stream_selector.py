import pytest
from backend.app.schemas.media import VideoMetadata, QualityOption, AudioOption, DownloadMode
from backend.app.media.stream_selector import select_streams

@pytest.fixture
def sample_metadata():
    return VideoMetadata(
        id="vid123",
        url="https://test-media.local/watch?v=123",
        title="Test Vid",
        channel="Test Channel",
        duration_seconds=120,
        source_provider="mock",
        video_options=[
            QualityOption(
                format_id="v_2160p",
                resolution="2160p",
                height=2160,
                width=3840,
                container="mp4",
                vcodec="av01",
                filesize_bytes=100000000,
                has_video=True,
                has_audio=False,
                requires_merging=True
            ),
            QualityOption(
                format_id="v_1080p",
                resolution="1080p",
                height=1080,
                width=1920,
                container="mp4",
                vcodec="avc1",
                filesize_bytes=50000000,
                has_video=True,
                has_audio=False,
                requires_merging=True
            ),
            QualityOption(
                format_id="v_720p_combined",
                resolution="720p",
                height=720,
                width=1280,
                container="mp4",
                vcodec="avc1",
                acodec="aac",
                filesize_bytes=25000000,
                has_video=True,
                has_audio=True,
                requires_merging=False
            )
        ],
        audio_options=[
            AudioOption(
                format_id="a_m4a_256",
                container="m4a",
                acodec="aac",
                abr_kbps=256,
                filesize_bytes=5000000,
                quality_label="256 kbps (Ultra)"
            ),
            AudioOption(
                format_id="a_opus_128",
                container="webm",
                acodec="opus",
                abr_kbps=128,
                filesize_bytes=2500000,
                quality_label="128 kbps (Standard)"
            )
        ]
    )

def test_select_1080p_video_audio(sample_metadata):
    result = select_streams(
        metadata=sample_metadata,
        mode=DownloadMode.VIDEO_AUDIO,
        requested_resolution="1080p",
        target_container="mp4"
    )
    assert result.video_format_id == "v_1080p"
    assert result.audio_format_id == "a_m4a_256"
    assert result.requires_merging is True
    # avc1 + aac into mp4 does NOT require conversion
    assert result.requires_conversion is False

def test_select_do_not_exceed_resolution(sample_metadata):
    # Requesting 720p should NOT return 1080p or 2160p
    result = select_streams(
        metadata=sample_metadata,
        mode=DownloadMode.VIDEO_AUDIO,
        requested_resolution="720p",
        target_container="mp4"
    )
    assert result.video_format_id == "v_720p_combined"
    assert result.requires_merging is False  # Already combined!

def test_audio_only_selection(sample_metadata):
    result = select_streams(
        metadata=sample_metadata,
        mode=DownloadMode.AUDIO_ONLY,
        target_container="mp3"
    )
    assert result.video_format_id is None
    assert result.audio_format_id == "a_m4a_256"
    # m4a to mp3 requires conversion
    assert result.requires_conversion is True

def test_video_only_selection(sample_metadata):
    result = select_streams(
        metadata=sample_metadata,
        mode=DownloadMode.VIDEO_ONLY,
        requested_resolution="1080p",
        target_container="mp4"
    )
    assert result.video_format_id == "v_1080p"
    assert result.audio_format_id is None
    assert result.requires_merging is False
