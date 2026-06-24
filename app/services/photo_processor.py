from PIL import Image

from app.models.schemas import DocumentSpecDetail, ValidationReport
from app.services.background import replace_background
from app.services.compliance import validate_processed_photo
from app.services.face_detection import FaceNotFoundError, detect_face_with_fallback
from app.services.smart_crop import smart_crop_to_document


def process_photo_for_document(
    image: Image.Image,
    document: DocumentSpecDetail,
) -> tuple[Image.Image, ValidationReport]:
    """
    Full pipeline: detect face → remove background → smart crop to spec → validate.
    """
    face = detect_face_with_fallback(image)
    bg_removed = replace_background(image, document.background_color)
    cropped, cropped_face = smart_crop_to_document(bg_removed, face, document)
    validation = validate_processed_photo(cropped, cropped_face, document)
    return cropped, validation


def process_photo_for_document_safe(
    image: Image.Image,
    document: DocumentSpecDetail,
) -> tuple[Image.Image | None, ValidationReport | None, str | None]:
    try:
        processed, validation = process_photo_for_document(image, document)
        return processed, validation, None
    except FaceNotFoundError as exc:
        return None, None, str(exc)
    except Exception as exc:  # noqa: BLE001
        return None, None, f"Processing failed: {exc}"
