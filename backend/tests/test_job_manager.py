import asyncio
import os
import uuid
import pytest
from backend.app.database.session import init_db
from backend.app.database.models import DownloadJobModel
from backend.app.database.session import AsyncSessionLocal
from backend.app.jobs.manager import job_manager
from backend.app.schemas.media import DownloadMode, JobStatus

@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()

async def test_job_execution_lifecycle():
    job_id = f"test_job_{uuid.uuid4().hex[:8]}"
    url = "https://test-media.local/watch?v=sample"

    # Insert initial DB record
    async with AsyncSessionLocal() as session:
        db_job = DownloadJobModel(
            id=job_id,
            url=url,
            mode=DownloadMode.VIDEO_AUDIO.value,
            resolution="1080p",
            target_container="mp4",
            status=JobStatus.QUEUED.value
        )
        session.add(db_job)
        await session.commit()

    # Start job
    await job_manager.start_job(
        job_id=job_id,
        url=url,
        mode=DownloadMode.VIDEO_AUDIO,
        resolution="1080p",
        target_container="mp4"
    )

    # Wait for completion (up to 10 seconds)
    completed = False
    for _ in range(50):
        progress = await job_manager.get_job_progress(job_id)
        if progress and progress.status == JobStatus.COMPLETED:
            completed = True
            break
        await asyncio.sleep(0.1)

    assert completed is True
    progress = await job_manager.get_job_progress(job_id)
    assert progress.progress_percent == 100.0
    assert progress.status == JobStatus.COMPLETED
    assert progress.file_name is not None
    assert progress.download_url == f"/api/downloads/{job_id}/file"

    # Verify output file exists
    assert progress.file_size_bytes is not None
    assert progress.file_size_bytes > 0
