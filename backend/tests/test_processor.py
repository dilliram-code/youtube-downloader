import asyncio
import os
import tempfile
import pytest
from backend.app.media.processor import processor, MediaProcessingError

@pytest.fixture
async def synthetic_media():
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "input_video.mp4")
        audio_path = os.path.join(tmpdir, "input_audio.m4a")

        # Generate 1s test video stream
        p1 = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=10",
            "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p", video_path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await p1.communicate()

        # Generate 1s test audio stream
        p2 = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", "1", "-c:a", "aac", audio_path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await p2.communicate()

        yield tmpdir, video_path, audio_path

async def test_merge_streams_and_validate(synthetic_media):
    tmpdir, video_path, audio_path = synthetic_media
    merged_output = os.path.join(tmpdir, "output_merged.mp4")

    out = await processor.merge_streams(
        video_path=video_path,
        audio_path=audio_path,
        output_path=merged_output,
        stream_copy=True,
        target_container="mp4"
    )
    assert os.path.exists(out)
    assert os.path.getsize(out) > 0

    # Probe and validate
    is_valid = await processor.validate_output(out, require_video=True, require_audio=True)
    assert is_valid is True

async def test_convert_audio_only(synthetic_media):
    tmpdir, _, audio_path = synthetic_media
    mp3_output = os.path.join(tmpdir, "output.mp3")

    out = await processor.convert_or_extract(
        input_path=audio_path,
        output_path=mp3_output,
        is_audio_only=True,
        target_container="mp3"
    )
    assert os.path.exists(out)
    meta = await processor.probe_file(out)
    streams = meta.get("streams", [])
    assert any(s.get("codec_name") == "mp3" for s in streams)

async def test_validate_output_corrupt(synthetic_media):
    tmpdir, _, _ = synthetic_media
    empty_file = os.path.join(tmpdir, "corrupt.mp4")
    with open(empty_file, "wb") as f:
        f.write(b"not a valid media file")

    with pytest.raises(MediaProcessingError):
        await processor.validate_output(empty_file)
