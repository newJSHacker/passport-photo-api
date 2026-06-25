from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.schemas import (
    CheckoutPricingResponse,
    CreateCheckoutSessionRequest,
    CreateCheckoutSessionResponse,
    OrderResponse,
)
from app.services.checkout import (
    create_checkout_session,
    get_order_by_job_response,
    get_order_by_session_response,
    get_order_response,
    get_pricing,
    handle_stripe_webhook,
)

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.get("/pricing", response_model=CheckoutPricingResponse)
async def checkout_pricing() -> CheckoutPricingResponse:
    return get_pricing()


@router.post("/sessions", response_model=CreateCheckoutSessionResponse)
async def create_checkout_session_endpoint(
    body: CreateCheckoutSessionRequest,
    session: AsyncSession = Depends(get_session),
) -> CreateCheckoutSessionResponse:
    return await create_checkout_session(
        session,
        photo_job_id=body.photo_job_id,
        email=body.email,
        delivery_type=body.delivery_type,
        print_copies=body.print_copies,
        addons=body.addons,
        success_url=body.success_url,
        cancel_url=body.cancel_url,
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_endpoint(
    order_id: str,
    session: AsyncSession = Depends(get_session),
) -> OrderResponse:
    return await get_order_response(session, order_id)


@router.get("/orders/by-job/{photo_job_id}", response_model=OrderResponse)
async def get_order_by_job_endpoint(
    photo_job_id: str,
    session: AsyncSession = Depends(get_session),
) -> OrderResponse:
    return await get_order_by_job_response(session, photo_job_id)


@router.get("/orders/by-session/{session_id}", response_model=OrderResponse)
async def get_order_by_session_endpoint(
    session_id: str,
    session: AsyncSession = Depends(get_session),
) -> OrderResponse:
    return await get_order_by_session_response(session, session_id)


@router.post("/webhook")
async def stripe_webhook_endpoint(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
) -> dict[str, str]:
    payload = await request.body()
    if not stripe_signature:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")
    await handle_stripe_webhook(payload, stripe_signature)
    return {"status": "ok"}
