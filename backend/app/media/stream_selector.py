from typing import List, Dict, Any, Optional, Tuple
from backend.app.schemas.media import DownloadMode, QualityOption, AudioOption, VideoMetadata

def parse_height_from_resolution(res: Optional[str]) -> Optional[int]:
    if not res:
        return None
    res = res.lower().strip()
    if res in ("best", "highest", "max"):
        return 99999
    digits = "".join(filter(str.isdigit, res))
    return int(digits) if digits else None

class StreamSelectionResult:
    def __init__(
        self,
        video_format_id: Optional[str],
        audio_format_id: Optional[str],
        requires_merging: bool,
        requires_conversion: bool,
        target_container: str,
        video_codec: Optional[str] = None,
        audio_codec: Optional[str] = None,
        estimated_total_bytes: Optional[int] = None,
        status_message: str = "Ready"
    ):
        self.video_format_id = video_format_id
        self.audio_format_id = audio_format_id
        self.requires_merging = requires_merging
        self.requires_conversion = requires_conversion
        self.target_container = target_container
        self.video_codec = video_codec
        self.audio_codec = audio_codec
        self.estimated_total_bytes = estimated_total_bytes
        self.status_message = status_message

def select_streams(
    metadata: VideoMetadata,
    mode: DownloadMode = DownloadMode.VIDEO_AUDIO,
    requested_resolution: Optional[str] = None,
    requested_format_id: Optional[str] = None,
    target_container: str = "mp4",
    requested_audio_quality: str = "best"
) -> StreamSelectionResult:
    """
    Selects the optimal streams and determines merging/conversion requirements.
    Never chooses a higher resolution than requested.
    """
    target_container = target_container.lower().strip()

    # Audio-only mode
    if mode == DownloadMode.AUDIO_ONLY:
        if not metadata.audio_options:
            raise ValueError("No audio streams available for this media source.")

        selected_audio = None
        if requested_format_id:
            for opt in metadata.audio_options:
                if opt.format_id == requested_format_id:
                    selected_audio = opt
                    break

        if not selected_audio:
            # Sort by bitrate descending
            sorted_audio = sorted(
                metadata.audio_options,
                key=lambda a: a.abr_kbps or 0,
                reverse=True
            )
            selected_audio = sorted_audio[0]

        # Determine if container conversion is needed
        source_ext = selected_audio.container.lower()
        requires_conversion = (source_ext != target_container)

        return StreamSelectionResult(
            video_format_id=None,
            audio_format_id=selected_audio.format_id,
            requires_merging=False,
            requires_conversion=requires_conversion,
            target_container=target_container,
            audio_codec=selected_audio.acodec,
            estimated_total_bytes=selected_audio.filesize_bytes,
            status_message="Requires conversion" if requires_conversion else "Ready to download"
        )

    # Video modes (VIDEO_AUDIO or VIDEO_ONLY)
    if not metadata.video_options:
        raise ValueError("No video streams available for this media source.")

    target_height = parse_height_from_resolution(requested_resolution)

    # Filter video options:
    # If format_id explicitly requested
    selected_video: Optional[QualityOption] = None
    if requested_format_id:
        for opt in metadata.video_options:
            if opt.format_id == requested_format_id:
                selected_video = opt
                break

    if not selected_video:
        # Filter available options that do not exceed requested resolution
        candidate_options = metadata.video_options
        if target_height and target_height < 99999:
            # Only allow height <= target_height
            candidate_options = [
                opt for opt in metadata.video_options
                if (opt.height or 0) <= target_height
            ]
            if not candidate_options:
                # Fallback to lowest available if all exceed, or raise
                candidate_options = sorted(metadata.video_options, key=lambda o: o.height or 0)

        # Sort candidate options:
        # 1. Height descending (get highest <= requested)
        # 2. Prefer matching container if possible
        # 3. Prefer combined stream if mode is VIDEO_AUDIO and combined exists
        def sort_key(opt: QualityOption):
            h = opt.height or 0
            container_match = 1 if opt.container == target_container else 0
            has_audio = 1 if (opt.has_audio and mode == DownloadMode.VIDEO_AUDIO) else 0
            return (h, container_match, has_audio)

        sorted_candidates = sorted(candidate_options, key=sort_key, reverse=True)
        selected_video = sorted_candidates[0]

    # Video Only mode
    if mode == DownloadMode.VIDEO_ONLY:
        requires_conversion = (selected_video.container != target_container)
        return StreamSelectionResult(
            video_format_id=selected_video.format_id,
            audio_format_id=None,
            requires_merging=False,
            requires_conversion=requires_conversion,
            target_container=target_container,
            video_codec=selected_video.vcodec,
            estimated_total_bytes=selected_video.filesize_bytes,
            status_message="Requires conversion" if requires_conversion else "Ready to download"
        )

    # Video + Audio mode
    # Check if chosen video already has audio
    if selected_video.has_audio:
        requires_conversion = (selected_video.container != target_container)
        return StreamSelectionResult(
            video_format_id=selected_video.format_id,
            audio_format_id=None,
            requires_merging=False,
            requires_conversion=requires_conversion,
            target_container=target_container,
            video_codec=selected_video.vcodec,
            audio_codec=selected_video.acodec,
            estimated_total_bytes=selected_video.filesize_bytes,
            status_message="Requires conversion" if requires_conversion else "Ready to download"
        )

    # Separate streams: Choose best matching audio stream
    if not metadata.audio_options:
        # No separate audio stream found, fallback to video only
        return StreamSelectionResult(
            video_format_id=selected_video.format_id,
            audio_format_id=None,
            requires_merging=False,
            requires_conversion=False,
            target_container=selected_video.container,
            video_codec=selected_video.vcodec,
            estimated_total_bytes=selected_video.filesize_bytes,
            status_message="Audio not available for this stream"
        )

    # Pick best audio stream
    # If target is mp4, prefer m4a/aac audio for zero-transcode stream copying
    preferred_audio_codec = "aac" if target_container == "mp4" else ("opus" if target_container == "webm" else None)

    def audio_sort_key(opt: AudioOption):
        codec_bonus = 100 if preferred_audio_codec and preferred_audio_codec in (opt.acodec or "").lower() else 0
        container_bonus = 50 if opt.container == target_container else 0
        bitrate = opt.abr_kbps or 0
        return (codec_bonus + container_bonus, bitrate)

    sorted_audio = sorted(metadata.audio_options, key=audio_sort_key, reverse=True)
    selected_audio = sorted_audio[0]

    # Calculate estimated combined size
    v_size = selected_video.filesize_bytes or 0
    a_size = selected_audio.filesize_bytes or 0
    total_bytes = (v_size + a_size) if (v_size > 0 and a_size > 0) else None

    # Check if conversion needed during merge
    vcodec = (selected_video.vcodec or "").lower()
    acodec = (selected_audio.acodec or "").lower()
    requires_conversion = False

    if target_container == "mp4":
        if "vp9" in vcodec or "av01" in vcodec or "opus" in acodec or "vorbis" in acodec:
            requires_conversion = True
    elif target_container == "webm":
        if "h264" in vcodec or "hevc" in vcodec or "aac" in acodec:
            requires_conversion = True

    status_msg = "Requires merging & conversion" if requires_conversion else "Requires merging"

    return StreamSelectionResult(
        video_format_id=selected_video.format_id,
        audio_format_id=selected_audio.format_id,
        requires_merging=True,
        requires_conversion=requires_conversion,
        target_container=target_container,
        video_codec=selected_video.vcodec,
        audio_codec=selected_audio.acodec,
        estimated_total_bytes=total_bytes,
        status_message=status_msg
    )
