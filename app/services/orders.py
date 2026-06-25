from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import OrderDB


async def get_order(session: AsyncSession, order_id: str) -> OrderDB | None:
    return await session.get(OrderDB, order_id)


async def get_order_by_stripe_session(
    session: AsyncSession,
    session_id: str,
) -> OrderDB | None:
    result = await session.execute(
        select(OrderDB).where(OrderDB.stripe_session_id == session_id),
    )
    return result.scalar_one_or_none()


async def get_paid_order_for_job(
    session: AsyncSession,
    photo_job_id: str,
) -> OrderDB | None:
    result = await session.execute(
        select(OrderDB)
        .where(OrderDB.photo_job_id == photo_job_id)
        .where(OrderDB.status == "paid")
        .order_by(OrderDB.paid_at.desc()),
    )
    return result.scalars().first()


async def mark_order_paid(
    session: AsyncSession,
    order: OrderDB,
    *,
    stripe_session_id: str | None = None,
) -> OrderDB:
    order.status = "paid"
    order.paid_at = datetime.now(UTC)
    if stripe_session_id:
        order.stripe_session_id = stripe_session_id
    await session.commit()
    await session.refresh(order)
    return order
