from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    CREATED = "created"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentDimensions(BaseModel):
    width_px: int
    height_px: int
    dpi: int = 300


class HeadRules(BaseModel):
    min_head_height_pct: float = Field(ge=0, le=100)
    max_head_height_pct: float = Field(ge=0, le=100)
    target_head_height_pct: float = Field(ge=0, le=100)
    eye_line_from_bottom_pct: float = Field(ge=0, le=100)
    eye_line_tolerance_pct: float = Field(ge=0, le=30, default=6)


class DocumentSpecSummary(BaseModel):
    id: str
    name: str
    country: str
    document_type: str
    dimensions: DocumentDimensions


class DocumentSpecDetail(DocumentSpecSummary):
    background_color: str
    head_rules: HeadRules
    description: str
    rules: list[str]


class ValidationIssue(BaseModel):
    code: str
    severity: Literal["error", "warning"]
    message: str


class ValidationReport(BaseModel):
    passed: bool
    score: int = Field(ge=0, le=100)
    issues: list[ValidationIssue] = []


class PhotoJobResponse(BaseModel):
    id: str
    document_id: str
    status: JobStatus
    created_at: str
    original_url: str | None = None
    processed_url: str | None = None
    preview_url: str | None = None
    validation: ValidationReport | None = None
    error: str | None = None


class CreatePhotoJobRequest(BaseModel):
    document_id: str


class CheckoutPricingOption(BaseModel):
    id: str
    title: str
    description: str
    amount_cents: int
    currency: str


class CheckoutPricingResponse(BaseModel):
    options: list[CheckoutPricingOption]


class CreateCheckoutSessionRequest(BaseModel):
    photo_job_id: str
    email: str = Field(min_length=3, max_length=255)
    delivery_type: Literal["digital", "print"]
    print_copies: Literal[2, 4, 6] | None = None
    addons: list[Literal["expert_check", "photo_retouching"]] = Field(default_factory=list)


class CreateCheckoutSessionResponse(BaseModel):
    order_id: str
    checkout_url: str
    demo_mode: bool = False
    photo_job_id: str | None = None
    email: str | None = None


class OrderResponse(BaseModel):
    id: str
    photo_job_id: str
    email: str
    delivery_type: str
    amount_cents: int
    currency: str
    status: str
    created_at: str
    paid_at: str | None = None
    download_url: str | None = None
