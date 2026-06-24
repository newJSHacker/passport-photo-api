from app.models.schemas import (
    DocumentDimensions,
    DocumentSpecDetail,
    DocumentSpecSummary,
    HeadRules,
)

US_HEAD_RULES = HeadRules(
    min_head_height_pct=50,
    max_head_height_pct=69,
    target_head_height_pct=60,
    eye_line_from_bottom_pct=62,
    eye_line_tolerance_pct=6,
)

UK_HEAD_RULES = HeadRules(
    min_head_height_pct=64.5,
    max_head_height_pct=75.5,
    target_head_height_pct=70,
    eye_line_from_bottom_pct=58,
    eye_line_tolerance_pct=5,
)

SCHENGEN_HEAD_RULES = HeadRules(
    min_head_height_pct=70,
    max_head_height_pct=80,
    target_head_height_pct=75,
    eye_line_from_bottom_pct=55,
    eye_line_tolerance_pct=5,
)

DOCUMENT_SPECS: dict[str, DocumentSpecDetail] = {
    "us-passport": DocumentSpecDetail(
        id="us-passport",
        name="US Passport Photo",
        country="US",
        document_type="passport",
        dimensions=DocumentDimensions(width_px=600, height_px=600, dpi=300),
        background_color="#FFFFFF",
        head_rules=US_HEAD_RULES,
        description="2×2 inch square photo for US passport applications.",
        rules=[
            "Plain white or off-white background",
            "Head height 50–69% of image",
            "Neutral expression, eyes open",
            "Taken within last 6 months",
        ],
    ),
    "us-visa": DocumentSpecDetail(
        id="us-visa",
        name="US Visa Photo",
        country="US",
        document_type="visa",
        dimensions=DocumentDimensions(width_px=600, height_px=600, dpi=300),
        background_color="#FFFFFF",
        head_rules=US_HEAD_RULES,
        description="2×2 inch photo for US visa applications.",
        rules=[
            "Plain white background",
            "Full face, no glasses glare",
            "No uniforms except religious attire",
        ],
    ),
    "uk-passport": DocumentSpecDetail(
        id="uk-passport",
        name="UK Passport Photo",
        country="GB",
        document_type="passport",
        dimensions=DocumentDimensions(width_px=413, height_px=531, dpi=300),
        background_color="#F0F0F0",
        head_rules=UK_HEAD_RULES,
        description="35×45 mm photo for UK passport applications.",
        rules=[
            "Plain cream or light grey background",
            "Head height 64.5–75.5% of image",
            "No smiling, mouth closed",
        ],
    ),
    "schengen-visa": DocumentSpecDetail(
        id="schengen-visa",
        name="Schengen Visa Photo",
        country="EU",
        document_type="visa",
        dimensions=DocumentDimensions(width_px=413, height_px=531, dpi=300),
        background_color="#F0F0F0",
        head_rules=SCHENGEN_HEAD_RULES,
        description="35×45 mm photo for Schengen visa applications.",
        rules=[
            "Light coloured background",
            "Face covers 70–80% of photo",
            "Recent photo, less than 6 months old",
        ],
    ),
    "india-passport": DocumentSpecDetail(
        id="india-passport",
        name="India Passport Photo",
        country="IN",
        document_type="passport",
        dimensions=DocumentDimensions(width_px=413, height_px=531, dpi=300),
        background_color="#FFFFFF",
        head_rules=UK_HEAD_RULES,
        description="35×45 mm photo for Indian passport applications.",
        rules=[
            "White background",
            "Matte finish, no shadows",
            "Both ears visible if possible",
        ],
    ),
}


def list_documents() -> list[DocumentSpecSummary]:
    return [
        DocumentSpecSummary(
            id=spec.id,
            name=spec.name,
            country=spec.country,
            document_type=spec.document_type,
            dimensions=spec.dimensions,
        )
        for spec in DOCUMENT_SPECS.values()
    ]


def get_document(document_id: str) -> DocumentSpecDetail | None:
    return DOCUMENT_SPECS.get(document_id)


def get_default_document_specs() -> list[DocumentSpecDetail]:
    return list(DOCUMENT_SPECS.values())
