from urllib.parse import quote

import uuid

import stripe
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import OrderDB, PhotoJobDB
from app.models.schemas import (
    CheckoutPricingOption,
    CheckoutPricingResponse,
    CreateCheckoutSessionResponse,
    JobStatus,
    OrderResponse,
)
from app.services.documents_db import get_document
from app.services.orders import get_order, get_order_by_stripe_session, mark_order_paid


PRINT_COPY_ADJUSTMENTS: dict[int, int] = {2: -400, 4: -150, 6: 400}

ADDON_PRICES: dict[str, int] = {
    "expert_check": settings.checkout_expert_check_price_cents,
    "photo_retouching": settings.checkout_retouching_price_cents,
}

ADDON_LABELS: dict[str, str] = {
    "expert_check": "Expert check & acceptance guarantee",
    "photo_retouching": "Photo retouching",
}


def get_pricing() -> CheckoutPricingResponse:
    currency = settings.checkout_currency
    return CheckoutPricingResponse(
        options=[
            CheckoutPricingOption(
                id="digital",
                title="Digital Photo",
                description="Instant online download. Ready for online submission and self-printing.",
                amount_cents=settings.checkout_digital_price_cents,
                currency=currency,
            ),
            CheckoutPricingOption(
                id="print",
                title="Digital Photo + Printouts",
                description="Printed photos with free delivery plus digital download.",
                amount_cents=settings.checkout_print_price_cents,
                currency=currency,
            ),
        ],
    )


def _price_for_delivery(delivery_type: str, print_copies: int | None = None) -> int:
    if delivery_type == "digital":
        return settings.checkout_digital_price_cents
    if delivery_type == "print":
        base = settings.checkout_print_price_cents
        copies = print_copies or 6
        return base + PRINT_COPY_ADJUSTMENTS.get(copies, 0)
    raise HTTPException(status_code=400, detail="Invalid delivery type")


def _product_name(document_name: str, delivery_type: str) -> str:
    suffix = "Print template" if delivery_type == "print" else "Digital download"
    return f"{document_name} — {suffix}"


def _addon_total(addons: list[str]) -> int:
    return sum(ADDON_PRICES.get(addon, 0) for addon in addons)


def _build_stripe_line_items(
    document_name: str,
    delivery_type: str,
    base_amount_cents: int,
    addons: list[str],
) -> list[dict]:
    items = [
        {
            "price_data": {
                "currency": settings.checkout_currency,
                "unit_amount": base_amount_cents,
                "product_data": {
                    "name": _product_name(document_name, delivery_type),
                },
            },
            "quantity": 1,
        },
    ]
    for addon in addons:
        price = ADDON_PRICES.get(addon)
        if not price:
            continue
        items.append(
            {
                "price_data": {
                    "currency": settings.checkout_currency,
                    "unit_amount": price,
                    "product_data": {"name": ADDON_LABELS[addon]},
                },
                "quantity": 1,
            },
        )
    return items


async def create_checkout_session(
    session: AsyncSession,
    *,
    photo_job_id: str,
    email: str,
    delivery_type: str,
    print_copies: int | None = None,
    addons: list[str] | None = None,
) -> CreateCheckoutSessionResponse:
    job = await session.get(PhotoJobDB, photo_job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Photo job not found")
    if job.status != JobStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Photo is not ready for checkout")

    document = await get_document(session, job.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document spec not found")

    selected_addons = addons or []
    base_amount_cents = _price_for_delivery(delivery_type, print_copies)
    amount_cents = base_amount_cents + _addon_total(selected_addons)
    order = OrderDB(
        id=str(uuid.uuid4()),
        photo_job_id=photo_job_id,
        email=email.strip(),
        delivery_type=delivery_type,
        amount_cents=amount_cents,
        currency=settings.checkout_currency,
        status="pending",
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)

    use_stripe = settings.stripe_enabled and not settings.checkout_demo_mode
    if not use_stripe:
        await mark_order_paid(session, order)
        success_url = (
            f"{settings.checkout_success_url.rstrip('/')}"
            f"?order_id={order.id}"
            f"&job_id={photo_job_id}"
            f"&email={quote(email.strip())}"
            f"&demo=1"
        )
        return CreateCheckoutSessionResponse(
            order_id=order.id,
            checkout_url=success_url,
            demo_mode=True,
            photo_job_id=photo_job_id,
            email=email.strip(),
        )

    stripe.api_key = settings.stripe_secret_key
    checkout_session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=email.strip(),
        line_items=_build_stripe_line_items(
            document.name,
            delivery_type,
            base_amount_cents,
            selected_addons,
        ),
        success_url=(
            f"{settings.checkout_success_url.rstrip('/')}"
            "?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=(
            f"{settings.checkout_cancel_url.rstrip('/')}"
            f"?job_id={photo_job_id}"
        ),
        metadata={
            "order_id": order.id,
            "photo_job_id": photo_job_id,
        },
    )

    order.stripe_session_id = checkout_session.id
    await session.commit()

    if not checkout_session.url:
        raise HTTPException(status_code=500, detail="Failed to create Stripe checkout")

    return CreateCheckoutSessionResponse(
        order_id=order.id,
        checkout_url=checkout_session.url,
        demo_mode=False,
    )


def order_to_response(order: OrderDB) -> OrderResponse:
    download_url = None
    if order.status == "paid":
        download_url = f"/api/v1/photos/{order.photo_job_id}/files/processed"

    created_at = order.created_at.isoformat() if order.created_at else ""
    paid_at = order.paid_at.isoformat() if order.paid_at else None

    return OrderResponse(
        id=order.id,
        photo_job_id=order.photo_job_id,
        email=order.email,
        delivery_type=order.delivery_type,
        amount_cents=order.amount_cents,
        currency=order.currency,
        status=order.status,
        created_at=created_at,
        paid_at=paid_at,
        download_url=download_url,
    )


async def get_order_by_job_response(
    session: AsyncSession,
    photo_job_id: str,
) -> OrderResponse:
    from app.services.orders import get_paid_order_for_job

    order = await get_paid_order_for_job(session, photo_job_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_to_response(order)


async def get_order_response(
    session: AsyncSession,
    order_id: str,
) -> OrderResponse:
    order = await get_order(session, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_to_response(order)


async def get_order_by_session_response(
    session: AsyncSession,
    stripe_session_id: str,
) -> OrderResponse:
    order = await get_order_by_stripe_session(session, stripe_session_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order = await _sync_order_payment_from_stripe(session, order)
    return order_to_response(order)


async def _sync_order_payment_from_stripe(
    session: AsyncSession,
    order: OrderDB,
) -> OrderDB:
    if order.status == "paid" or not settings.stripe_enabled:
        return order
    if not order.stripe_session_id:
        return order

    stripe.api_key = settings.stripe_secret_key
    checkout_session = stripe.checkout.Session.retrieve(order.stripe_session_id)
    if checkout_session.payment_status == "paid":
        return await mark_order_paid(
            session,
            order,
            stripe_session_id=order.stripe_session_id,
        )
    return order


async def handle_stripe_webhook(payload: bytes, signature: str) -> None:
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=400, detail="Webhook not configured")

    stripe.api_key = settings.stripe_secret_key
    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.stripe_webhook_secret,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid payload") from exc
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail="Invalid signature") from exc

    if event["type"] != "checkout.session.completed":
        return

    checkout_session = event["data"]["object"]
    order_id = checkout_session.get("metadata", {}).get("order_id")
    if not order_id:
        return

    from app.db import AsyncSessionLocal

    async with AsyncSessionLocal() as db_session:
        order = await get_order(db_session, order_id)
        if order and order.status != "paid":
            await mark_order_paid(
                db_session,
                order,
                stripe_session_id=checkout_session.get("id"),
            )
