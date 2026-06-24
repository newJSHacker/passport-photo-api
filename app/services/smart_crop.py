import numpy as np
from PIL import Image

from app.models.schemas import DocumentSpecDetail, HeadRules
from app.services.face_detection import FaceMetrics


def smart_crop_to_document(
    image: Image.Image,
    face: FaceMetrics,
    document: DocumentSpecDetail,
) -> tuple[Image.Image, FaceMetrics]:
    rules = document.head_rules
    out_w = document.dimensions.width_px
    out_h = document.dimensions.height_px

    target_head_px = out_h * (rules.target_head_height_pct / 100.0)
    scale = target_head_px / face.head_height

    scaled_w = int(round(image.width * scale))
    scaled_h = int(round(image.height * scale))
    scaled = image.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

    scaled_face = _scale_face_metrics(face, scale)

    eye_y_from_bottom = out_h - scaled_face.eye_center_y
    target_eye_from_bottom = out_h * (rules.eye_line_from_bottom_pct / 100.0)
    shift_y = int(round(eye_y_from_bottom - target_eye_from_bottom))

    crop_left = int(round(scaled_face.eye_center_x - out_w / 2))
    crop_top = shift_y

    canvas = Image.new("RGB", (out_w, out_h), _hex_to_rgb(document.background_color))
    canvas.paste(
        scaled,
        (-crop_left, -crop_top),
    )

    cropped_face = _translate_face_metrics(scaled_face, -crop_left, -crop_top)
    return canvas, cropped_face


def _scale_face_metrics(face: FaceMetrics, scale: float) -> FaceMetrics:
    return FaceMetrics(
        face_center_x=face.face_center_x * scale,
        eye_center_x=face.eye_center_x * scale,
        eye_center_y=face.eye_center_y * scale,
        chin_y=face.chin_y * scale,
        head_top_y=face.head_top_y * scale,
        head_height=face.head_height * scale,
        face_width=face.face_width * scale,
        confidence=face.confidence,
    )


def _translate_face_metrics(
    face: FaceMetrics, dx: float, dy: float
) -> FaceMetrics:
    return FaceMetrics(
        face_center_x=face.face_center_x + dx,
        eye_center_x=face.eye_center_x + dx,
        eye_center_y=face.eye_center_y + dy,
        chin_y=face.chin_y + dy,
        head_top_y=face.head_top_y + dy,
        head_height=face.head_height,
        face_width=face.face_width,
        confidence=face.confidence,
    )


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
