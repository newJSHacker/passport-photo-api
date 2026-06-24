from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.schemas import DocumentSpecDetail, DocumentSpecSummary
from app.services.documents_db import (
    create_document,
    delete_document,
    get_document,
    list_documents,
    update_document,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentSpecSummary])
async def get_documents(
    session: AsyncSession = Depends(get_session),
) -> list[DocumentSpecSummary]:
    return await list_documents(session)


@router.get("/{document_id}", response_model=DocumentSpecDetail)
async def get_document_by_id(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> DocumentSpecDetail:
    document = await get_document(session, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("", response_model=DocumentSpecDetail, status_code=201)
async def create_document_spec(
    body: DocumentSpecDetail,
    session: AsyncSession = Depends(get_session),
) -> DocumentSpecDetail:
    existing = await get_document(session, body.id)
    if existing:
        raise HTTPException(status_code=409, detail="Document with this id already exists")

    try:
        return await create_document(session, body)
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Could not create document") from exc


@router.put("/{document_id}", response_model=DocumentSpecDetail)
async def update_document_spec(
    document_id: str,
    body: DocumentSpecDetail,
    session: AsyncSession = Depends(get_session),
) -> DocumentSpecDetail:
    if body.id != document_id:
        raise HTTPException(status_code=400, detail="Body id must match path document_id")

    updated = await update_document(session, document_id, body)
    if not updated:
        raise HTTPException(status_code=404, detail="Document not found")
    return updated


@router.delete("/{document_id}", status_code=204)
async def delete_document_spec(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        deleted = await delete_document(session, document_id)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Document is in use by existing jobs and cannot be deleted",
        ) from exc

    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
