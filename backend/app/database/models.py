from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

def utcnow():
    return datetime.now(timezone.utc)

class DownloadJobModel(Base):
    __tablename__ = "download_jobs"

    id = Column(String(64), primary_key=True, index=True)
    url = Column(String(2048), nullable=False)
    video_title = Column(String(512), default="Untitled")
    channel = Column(String(256), nullable=True)
    thumbnail = Column(String(1024), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    mode = Column(String(32), default="video_audio")
    resolution = Column(String(32), nullable=True)
    target_container = Column(String(16), default="mp4")
    format_id = Column(String(64), nullable=True)
    audio_format_id = Column(String(64), nullable=True)

    status = Column(String(32), default="queued", index=True)
    stage_label = Column(String(64), default="Queued")
    progress_percent = Column(Float, default=0.0)
    downloaded_bytes = Column(Integer, default=0)
    total_bytes = Column(Integer, default=0)
    download_speed_bytes = Column(Float, default=0.0)
    eta_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    output_filename = Column(String(256), nullable=True)
    output_filepath = Column(String(1024), nullable=True)
    output_filesize_bytes = Column(Integer, nullable=True)
    is_expired = Column(Boolean, default=False)

    created_at = Column(DateTime, default=utcnow, index=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
