from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings
from app.services.document_specs import get_default_document_specs


class Base(DeclarativeBase):
    pass


class DocumentSpecDB(Base):
    __tablename__ = "document_specs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(16), nullable=False)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    width_px: Mapped[int] = mapped_column(nullable=False)
    height_px: Mapped[int] = mapped_column(nullable=False)
    dpi: Mapped[int] = mapped_column(nullable=False, default=300)
    background_color: Mapped[str] = mapped_column(String(16), nullable=False)
    head_rules: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rules: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


class PhotoJobDB(Base):
    __tablename__ = "photo_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("document_specs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    original_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    preview_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class OrderDB(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    photo_job_id: Mapped[str] = mapped_column(
        ForeignKey("photo_jobs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    delivery_type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount_cents: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="usd")
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    stripe_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


engine = create_async_engine(settings.database_url, future=True, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def seed_document_specs(session: AsyncSession) -> None:
    existing_count = await session.scalar(select(func.count()).select_from(DocumentSpecDB))
    if existing_count and existing_count > 0:
        return

    for spec in get_default_document_specs():
        session.add(
            DocumentSpecDB(
                id=spec.id,
                name=spec.name,
                country=spec.country,
                document_type=spec.document_type,
                width_px=spec.dimensions.width_px,
                height_px=spec.dimensions.height_px,
                dpi=spec.dimensions.dpi,
                background_color=spec.background_color,
                head_rules=spec.head_rules.model_dump(),
                description=spec.description,
                rules=spec.rules,
            ),
        )

    await session.commit()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_document_specs(session)
