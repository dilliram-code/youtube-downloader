import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger

class MediaProcessingError(Exception):
    pass

class MediaProcessor:
    def __init__(self, ffmpeg_path: Optional[str] = None, ffprobe_path: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_path or settings.FFMPEG_PATH
        self.ffprobe_path = ffprobe_path or settings.FFPROBE_PATH

    async def probe_file(self, file_path: str) -> Dict[str, Any]:
        """
        Runs ffprobe without shell interpolation and returns parsed metadata.
        """
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            raise MediaProcessingError(f"Target media file does not exist or is empty: {file_path}")

        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err_msg = stderr.decode(errors="replace").strip()
            raise MediaProcessingError(f"ffprobe failed with exit code {proc.returncode}: {err_msg}")

        try:
            return json.loads(stdout.decode())
        except json.JSONDecodeError as e:
            raise MediaProcessingError(f"Failed to parse ffprobe output: {e}")

    async def validate_output(
        self,
        file_path: str,
        require_video: bool = True,
        require_audio: bool = True
    ) -> bool:
        """
        Validates that generated output exists, is readable, and contains the required stream types.
        """
        meta = await self.probe_file(file_path)
        streams = meta.get("streams", [])

        has_video = any(s.get("codec_type") == "video" for s in streams)
        has_audio = any(s.get("codec_type") == "audio" for s in streams)

        if require_video and not has_video:
            raise MediaProcessingError("Output validation failed: Expected video stream was not found")

        if require_audio and not has_audio:
            raise MediaProcessingError("Output validation failed: Expected audio stream was not found")

        format_info = meta.get("format", {})
        duration = float(format_info.get("duration", 0))
        if duration <= 0:
            raise MediaProcessingError("Output validation failed: Media has zero duration or is corrupt")

        return True

    async def merge_streams(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        stream_copy: bool = True,
        target_container: str = "mp4"
    ) -> str:
        """
        Merges separate video and audio streams using FFmpeg.
        Uses stream copying if compatible, otherwise transcodes safely.
        """
        if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
            raise MediaProcessingError(f"Video input file is missing or empty: {video_path}")
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            raise MediaProcessingError(f"Audio input file is missing or empty: {audio_path}")

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_path,
            "-y",  # overwrite output if exists
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v:0",
            "-map", "1:a:0"
        ]

        if stream_copy:
            cmd.extend(["-c", "copy"])
        else:
            # Safe transcoding based on container
            if target_container == "mp4":
                cmd.extend(["-c:v", "libx264", "-c:a", "aac", "-preset", "fast"])
            elif target_container == "webm":
                cmd.extend(["-c:v", "libvpx-vp9", "-c:a", "libopus"])
            else:
                cmd.extend(["-c:v", "copy", "-c:a", "aac"])

        if target_container == "mp4":
            cmd.extend(["-movflags", "+faststart"])

        cmd.append(output_path)

        logger.info(f"Executing FFmpeg merge: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            err_msg = stderr.decode(errors="replace").strip()
            raise MediaProcessingError(f"FFmpeg merge failed: {err_msg}")

        # Validate output
        await self.validate_output(output_path, require_video=True, require_audio=True)
        return output_path

    async def convert_or_extract(
        self,
        input_path: str,
        output_path: str,
        is_audio_only: bool = False,
        target_container: str = "mp4"
    ) -> str:
        """
        Converts media file or extracts audio to target container.
        """
        if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
            raise MediaProcessingError(f"Input file missing or empty: {input_path}")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [self.ffmpeg_path, "-y", "-i", input_path]

        if is_audio_only:
            cmd.append("-vn")
            if target_container == "mp3":
                cmd.extend(["-c:a", "libmp3lame", "-q:a", "2"])
            elif target_container in ("m4a", "aac"):
                cmd.extend(["-c:a", "aac", "-b:a", "192k"])
            elif target_container == "opus":
                cmd.extend(["-c:a", "libopus", "-b:a", "128k"])
            elif target_container == "wav":
                cmd.extend(["-c:a", "pcm_s16le"])
            else:
                cmd.extend(["-c:a", "copy"])
        else:
            if target_container == "mp4":
                cmd.extend(["-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", "-preset", "fast"])
            elif target_container == "webm":
                cmd.extend(["-c:v", "libvpx-vp9", "-c:a", "libopus"])
            else:
                cmd.extend(["-c", "copy"])

        cmd.append(output_path)

        logger.info(f"Executing FFmpeg convert: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            err_msg = stderr.decode(errors="replace").strip()
            raise MediaProcessingError(f"FFmpeg conversion failed: {err_msg}")

        await self.validate_output(
            output_path,
            require_video=not is_audio_only,
            require_audio=True
        )
        return output_path

processor = MediaProcessor()
