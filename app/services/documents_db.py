from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import DocumentSpecDB
from app.models.schemas import (
    DocumentDimensions,
    DocumentSpecDetail,
    DocumentSpecSummary,
    HeadRules,
)


def to_document_summary(document: DocumentSpecDB) -> DocumentSpecSummary:
    return DocumentSpecSummary(
        id=document.id,
        name=document.name,
        country=document.country,
        document_type=document.document_type,
        dimensions=DocumentDimensions(
            width_px=document.width_px,
            height_px=document.height_px,
            dpi=document.dpi,
        ),
    )


def to_document_detail(document: DocumentSpecDB) -> DocumentSpecDetail:
    return DocumentSpecDetail(
        id=document.id,
        name=document.name,
        country=document.country,
        document_type=document.document_type,
        dimensions=DocumentDimensions(
            width_px=document.width_px,
            height_px=document.height_px,
            dpi=document.dpi,
        ),
        background_color=document.background_color,
        head_rules=HeadRules(**document.head_rules),
        description=document.description,
        rules=document.rules,
    )


def apply_document_detail(document: DocumentSpecDB, payload: DocumentSpecDetail) -> None:
    document.name = payload.name
    document.country = payload.country
    document.document_type = payload.document_type
    document.width_px = payload.dimensions.width_px
    document.height_px = payload.dimensions.height_px
    document.dpi = payload.dimensions.dpi
    document.background_color = payload.background_color
    document.head_rules = payload.head_rules.model_dump()
    document.description = payload.description
    document.rules = payload.rules


async def list_documents(session: AsyncSession) -> list[DocumentSpecSummary]:
    result = await session.execute(select(DocumentSpecDB).order_by(DocumentSpecDB.name))
    documents = result.scalars().all()
    return [to_document_summary(document) for document in documents]


async def get_document(session: AsyncSession, document_id: str) -> DocumentSpecDetail | None:
    document = await session.get(DocumentSpecDB, document_id)
    if not document:
        return None
    return to_document_detail(document)


async def create_document(
    session: AsyncSession,
    payload: DocumentSpecDetail,
) -> DocumentSpecDetail:
    document = DocumentSpecDB(
        id=payload.id,
        name=payload.name,
        country=payload.country,
        document_type=payload.document_type,
        width_px=payload.dimensions.width_px,
        height_px=payload.dimensions.height_px,
        dpi=payload.dimensions.dpi,
        background_color=payload.background_color,
        head_rules=payload.head_rules.model_dump(),
        description=payload.description,
        rules=payload.rules,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return to_document_detail(document)


async def update_document(
    session: AsyncSession,
    document_id: str,
    payload: DocumentSpecDetail,
) -> DocumentSpecDetail | None:
    document = await session.get(DocumentSpecDB, document_id)
    if not document:
        return None

    apply_document_detail(document, payload)
    await session.commit()
    await session.refresh(document)
    return to_document_detail(document)


async def delete_document(session: AsyncSession, document_id: str) -> bool:
    document = await session.get(DocumentSpecDB, document_id)
    if not document:
        return False
    await session.delete(document)
    await session.commit()
    return True
