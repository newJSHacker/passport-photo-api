"""init schema

Revision ID: 20260624_0001
Revises:
Create Date: 2026-06-24 22:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260624_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_specs",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=16), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("width_px", sa.Integer(), nullable=False),
        sa.Column("height_px", sa.Integer(), nullable=False),
        sa.Column("dpi", sa.Integer(), nullable=False, server_default=sa.text("300")),
        sa.Column("background_color", sa.String(length=16), nullable=False),
        sa.Column("head_rules", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
    )

    op.create_table(
        "photo_jobs",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("original_path", sa.Text(), nullable=True),
        sa.Column("processed_path", sa.Text(), nullable=True),
        sa.Column("preview_path", sa.Text(), nullable=True),
        sa.Column("validation", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["document_specs.id"],
            name="fk_photo_jobs_document_id_document_specs",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_photo_jobs_document_id", "photo_jobs", ["document_id"])
    op.create_index("ix_photo_jobs_status", "photo_jobs", ["status"])
    op.create_index("ix_photo_jobs_created_at", "photo_jobs", ["created_at"])

    document_specs_table = sa.table(
        "document_specs",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("country", sa.String),
        sa.column("document_type", sa.String),
        sa.column("width_px", sa.Integer),
        sa.column("height_px", sa.Integer),
        sa.column("dpi", sa.Integer),
        sa.column("background_color", sa.String),
        sa.column("head_rules", sa.JSON),
        sa.column("description", sa.Text),
        sa.column("rules", sa.JSON),
    )

    op.bulk_insert(
        document_specs_table,
        [
            {
                "id": "us-passport",
                "name": "US Passport Photo",
                "country": "US",
                "document_type": "passport",
                "width_px": 600,
                "height_px": 600,
                "dpi": 300,
                "background_color": "#FFFFFF",
                "head_rules": {
                    "min_head_height_pct": 50,
                    "max_head_height_pct": 69,
                    "target_head_height_pct": 60,
                    "eye_line_from_bottom_pct": 62,
                    "eye_line_tolerance_pct": 6,
                },
                "description": "2×2 inch square photo for US passport applications.",
                "rules": [
                    "Plain white or off-white background",
                    "Head height 50–69% of image",
                    "Neutral expression, eyes open",
                    "Taken within last 6 months",
                ],
            },
            {
                "id": "us-visa",
                "name": "US Visa Photo",
                "country": "US",
                "document_type": "visa",
                "width_px": 600,
                "height_px": 600,
                "dpi": 300,
                "background_color": "#FFFFFF",
                "head_rules": {
                    "min_head_height_pct": 50,
                    "max_head_height_pct": 69,
                    "target_head_height_pct": 60,
                    "eye_line_from_bottom_pct": 62,
                    "eye_line_tolerance_pct": 6,
                },
                "description": "2×2 inch photo for US visa applications.",
                "rules": [
                    "Plain white background",
                    "Full face, no glasses glare",
                    "No uniforms except religious attire",
                ],
            },
            {
                "id": "uk-passport",
                "name": "UK Passport Photo",
                "country": "GB",
                "document_type": "passport",
                "width_px": 413,
                "height_px": 531,
                "dpi": 300,
                "background_color": "#F0F0F0",
                "head_rules": {
                    "min_head_height_pct": 64.5,
                    "max_head_height_pct": 75.5,
                    "target_head_height_pct": 70,
                    "eye_line_from_bottom_pct": 58,
                    "eye_line_tolerance_pct": 5,
                },
                "description": "35×45 mm photo for UK passport applications.",
                "rules": [
                    "Plain cream or light grey background",
                    "Head height 64.5–75.5% of image",
                    "No smiling, mouth closed",
                ],
            },
            {
                "id": "schengen-visa",
                "name": "Schengen Visa Photo",
                "country": "EU",
                "document_type": "visa",
                "width_px": 413,
                "height_px": 531,
                "dpi": 300,
                "background_color": "#F0F0F0",
                "head_rules": {
                    "min_head_height_pct": 70,
                    "max_head_height_pct": 80,
                    "target_head_height_pct": 75,
                    "eye_line_from_bottom_pct": 55,
                    "eye_line_tolerance_pct": 5,
                },
                "description": "35×45 mm photo for Schengen visa applications.",
                "rules": [
                    "Light coloured background",
                    "Face covers 70–80% of photo",
                    "Recent photo, less than 6 months old",
                ],
            },
            {
                "id": "india-passport",
                "name": "India Passport Photo",
                "country": "IN",
                "document_type": "passport",
                "width_px": 413,
                "height_px": 531,
                "dpi": 300,
                "background_color": "#FFFFFF",
                "head_rules": {
                    "min_head_height_pct": 64.5,
                    "max_head_height_pct": 75.5,
                    "target_head_height_pct": 70,
                    "eye_line_from_bottom_pct": 58,
                    "eye_line_tolerance_pct": 5,
                },
                "description": "35×45 mm photo for Indian passport applications.",
                "rules": [
                    "White background",
                    "Matte finish, no shadows",
                    "Both ears visible if possible",
                ],
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_photo_jobs_created_at", table_name="photo_jobs")
    op.drop_index("ix_photo_jobs_status", table_name="photo_jobs")
    op.drop_index("ix_photo_jobs_document_id", table_name="photo_jobs")
    op.drop_table("photo_jobs")
    op.drop_table("document_specs")
