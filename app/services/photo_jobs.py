import uuid

from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import PhotoJobDB
from app.models.schemas import JobStatus, PhotoJobResponse
from app.services.documents_db import get_document
from app.services.photo_processor import process_photo_for_document


async def create_photo_job(session: AsyncSession, document_id: str) -> PhotoJobDB:
    document = await get_document(session, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document spec not found")

    job = PhotoJobDB(
        id=str(uuid.uuid4()),
        document_id=document_id,
        status=JobStatus.CREATED.value,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_photo_job(session: AsyncSession, job_id: str) -> PhotoJobDB:
    job = await session.get(PhotoJobDB, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Photo job not found")
    return job


async def list_photo_jobs(
    session: AsyncSession,
    status: JobStatus | None = None,
    limit: int = 100,
) -> list[PhotoJobDB]:
    query = select(PhotoJobDB).order_by(desc(PhotoJobDB.created_at)).limit(limit)
    if status is not None:
        query = query.where(PhotoJobDB.status == status.value)

    result = await session.execute(query)
    return list(result.scalars().all())


async def save_upload(
    session: AsyncSession,
    job_id: str,
    upload: UploadFile,
) -> PhotoJobDB:
    job = await get_photo_job(session, job_id)

    if not upload.content_type or not upload.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    content = await upload.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds {settings.max_upload_mb}MB limit",
        )

    job_dir = Path(settings.storage_path) / job.id
    job_dir.mkdir(parents=True, exist_ok=True)
    original_path = job_dir / "original.jpg"
    original_path.write_bytes(content)

    job.original_path = str(original_path)
    job.status = JobStatus.UPLOADED.value
    await session.commit()
    await session.refresh(job)
    return job


async def process_photo(session: AsyncSession, job_id: str) -> PhotoJobDB:
    job = await get_photo_job(session, job_id)
    status = JobStatus(job.status)

    if status not in {JobStatus.UPLOADED, JobStatus.FAILED}:
        raise HTTPException(status_code=400, detail="Job is not ready for processing")

    if not job.original_path:
        raise HTTPException(status_code=400, detail="No uploaded image found")

    document = await get_document(session, job.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document spec not found")

    job.status = JobStatus.PROCESSING.value
    await session.commit()

    try:
        job_dir = Path(settings.storage_path) / job.id
        processed_path = job_dir / "processed.jpg"
        preview_path = job_dir / "preview.jpg"

        with Image.open(job.original_path) as image:
            image = image.convert("RGB")
            processed, validation = process_photo_for_document(image, document)

        dpi = (document.dimensions.dpi, document.dimensions.dpi)
        processed.save(processed_path, format="JPEG", quality=95, dpi=dpi)
        processed.save(preview_path, format="JPEG", quality=85, dpi=dpi)

        job.processed_path = str(processed_path)
        job.preview_path = str(preview_path)
        job.validation = validation.model_dump()
        job.status = JobStatus.COMPLETED.value
        job.error = None
    except Exception as exc:  # noqa: BLE001
        job.status = JobStatus.FAILED.value
        job.error = str(exc)

    await session.commit()
    await session.refresh(job)
    return job


def to_response(job: PhotoJobDB) -> PhotoJobResponse:
    base = f"/api/v1/photos/{job.id}/files"
    created_at = (
        job.created_at.isoformat() if job.created_at else ""
    )
    return PhotoJobResponse(
        id=job.id,
        document_id=job.document_id,
        status=JobStatus(job.status),
        created_at=created_at,
        original_url=f"{base}/original" if job.original_path else None,
        processed_url=f"{base}/processed" if job.processed_path else None,
        preview_url=f"{base}/preview" if job.preview_path else None,
        validation=job.validation,
        error=job.error,
    )


