from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.schemas import CreatePhotoJobRequest, JobStatus, PhotoJobResponse
from app.services.photo_jobs import (
    create_photo_job,
    get_photo_job,
    list_photo_jobs as list_photo_jobs_db,
    process_photo,
    save_upload,
    to_response,
)

router = APIRouter(prefix="/photos", tags=["photos"])


@router.post("", response_model=PhotoJobResponse, status_code=201)
async def create_photo_job_endpoint(
    body: CreatePhotoJobRequest,
    session: AsyncSession = Depends(get_session),
) -> PhotoJobResponse:
    job = await create_photo_job(session, body.document_id)
    return to_response(job)


@router.get("", response_model=list[PhotoJobResponse])
async def list_photo_jobs(
    status: JobStatus | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> list[PhotoJobResponse]:
    jobs = await list_photo_jobs_db(session, status=status, limit=limit)
    return [to_response(job) for job in jobs]


@router.post("/{job_id}/upload", response_model=PhotoJobResponse)
async def upload_photo(
    job_id: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> PhotoJobResponse:
    job = await save_upload(session, job_id, file)
    return to_response(job)


@router.post("/{job_id}/process", response_model=PhotoJobResponse)
async def process_photo_endpoint(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> PhotoJobResponse:
    job = await process_photo(session, job_id)
    return to_response(job)


@router.get("/{job_id}", response_model=PhotoJobResponse)
async def get_photo_job_endpoint(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> PhotoJobResponse:
    job = await get_photo_job(session, job_id)
    return to_response(job)


@router.get("/{job_id}/files/{file_type}")
async def get_photo_file(
    job_id: str,
    file_type: str,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    job = await get_photo_job(session, job_id)
    path_map = {
        "original": job.original_path,
        "processed": job.processed_path,
        "preview": job.preview_path,
    }
    file_path = path_map.get(file_type)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type="image/jpeg")
