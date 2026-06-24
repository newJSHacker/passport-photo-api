from PIL import Image

from app.models.schemas import DocumentSpecDetail, ValidationIssue, ValidationReport
from app.services.face_detection import FaceMetrics, detect_face_with_fallback


def validate_processed_photo(
    image: Image.Image,
    face: FaceMetrics,
    document: DocumentSpecDetail,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    out_h = document.dimensions.height_px
    rules = document.head_rules

    head_height_pct = (face.head_height / out_h) * 100.0
    eye_from_bottom_pct = ((out_h - face.eye_center_y) / out_h) * 100.0

    if head_height_pct < rules.min_head_height_pct:
        issues.append(
            ValidationIssue(
                code="HEAD_TOO_SMALL",
                severity="error",
                message=(
                    f"Head height is {head_height_pct:.1f}% of photo; "
                    f"minimum is {rules.min_head_height_pct:.0f}%. Move closer to the camera."
                ),
            )
        )
    elif head_height_pct > rules.max_head_height_pct:
        issues.append(
            ValidationIssue(
                code="HEAD_TOO_LARGE",
                severity="error",
                message=(
                    f"Head height is {head_height_pct:.1f}% of photo; "
                    f"maximum is {rules.max_head_height_pct:.0f}%. Move farther from the camera."
                ),
            )
        )

    eye_min = rules.eye_line_from_bottom_pct - rules.eye_line_tolerance_pct
    eye_max = rules.eye_line_from_bottom_pct + rules.eye_line_tolerance_pct
    if eye_from_bottom_pct < eye_min or eye_from_bottom_pct > eye_max:
        issues.append(
            ValidationIssue(
                code="EYE_LINE_OFF",
                severity="warning",
                message=(
                    f"Eye line is {eye_from_bottom_pct:.1f}% from bottom; "
                    f"target is {rules.eye_line_from_bottom_pct:.0f}% "
                    f"(±{rules.eye_line_tolerance_pct:.0f}%)."
                ),
            )
        )

    if face.confidence < 0.7:
        issues.append(
            ValidationIssue(
                code="LOW_FACE_CONFIDENCE",
                severity="warning",
                message="Face detection confidence is low. Retake with better lighting.",
            )
        )

    if image.width != document.dimensions.width_px or image.height != document.dimensions.height_px:
        issues.append(
            ValidationIssue(
                code="DIMENSIONS_MISMATCH",
                severity="error",
                message="Output dimensions do not match document specification.",
            )
        )

    # Verify face remains visible in the final output.
    try:
        detect_face_with_fallback(image)
    except Exception:  # noqa: BLE001
        issues.append(
            ValidationIssue(
                code="FACE_NOT_VISIBLE",
                severity="error",
                message="Face is not clearly visible in the processed photo.",
            )
        )

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    passed = len(errors) == 0

    score = 100
    score -= len(errors) * 25
    score -= len(warnings) * 8
    score = max(0, min(100, score))

    return ValidationReport(passed=passed, score=score, issues=issues)
