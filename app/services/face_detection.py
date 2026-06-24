from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image

# MediaPipe Face Mesh landmark indices
_CHIN = 152
_FOREHEAD = 10
_LEFT_EYE_OUTER = 33
_RIGHT_EYE_OUTER = 263
_LEFT_EYE_INNER = 133
_RIGHT_EYE_INNER = 362

_face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
)


@dataclass(frozen=True)
class FaceMetrics:
    face_center_x: float
    eye_center_x: float
    eye_center_y: float
    chin_y: float
    head_top_y: float
    head_height: float
    face_width: float
    confidence: float


class FaceNotFoundError(Exception):
    pass


def _landmark_xy(landmark, width: int, height: int) -> tuple[float, float]:
    return landmark.x * width, landmark.y * height


def detect_face(image: Image.Image) -> FaceMetrics:
    rgb = np.array(image.convert("RGB"))
    height, width = rgb.shape[:2]
    results = _face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        raise FaceNotFoundError("No face detected. Use a clear front-facing portrait.")

    landmarks = results.multi_face_landmarks[0].landmark

    left_eye = _landmark_xy(landmarks[_LEFT_EYE_OUTER], width, height)
    right_eye = _landmark_xy(landmarks[_RIGHT_EYE_OUTER], width, height)
    left_inner = _landmark_xy(landmarks[_LEFT_EYE_INNER], width, height)
    right_inner = _landmark_xy(landmarks[_RIGHT_EYE_INNER], width, height)
    chin = _landmark_xy(landmarks[_CHIN], width, height)
    forehead = _landmark_xy(landmarks[_FOREHEAD], width, height)

    eye_center_x = (left_inner[0] + right_inner[0]) / 2
    eye_center_y = (left_inner[1] + right_inner[1]) / 2

    # Extend above forehead to approximate top of head (hairline/crown).
    face_span = chin[1] - forehead[1]
    head_top_y = max(0.0, forehead[1] - face_span * 0.35)

    head_height = max(chin[1] - head_top_y, 1.0)
    face_width = max(abs(right_eye[0] - left_eye[0]) * 1.8, 1.0)
    face_center_x = (left_eye[0] + right_eye[0]) / 2

    return FaceMetrics(
        face_center_x=face_center_x,
        eye_center_x=eye_center_x,
        eye_center_y=eye_center_y,
        chin_y=chin[1],
        head_top_y=head_top_y,
        head_height=head_height,
        face_width=face_width,
        confidence=0.9,
    )


def detect_face_with_fallback(image: Image.Image) -> FaceMetrics:
    try:
        return detect_face(image)
    except FaceNotFoundError:
        return _detect_face_opencv(image)


def _detect_face_opencv(image: Image.Image) -> FaceMetrics:
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    gray = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    if len(faces) == 0:
        raise FaceNotFoundError("No face detected. Use a clear front-facing portrait.")

    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    eye_center_x = x + w / 2
    eye_center_y = y + h * 0.38
    head_top_y = float(y)
    chin_y = float(y + h)
    head_height = float(h)

    return FaceMetrics(
        face_center_x=eye_center_x,
        eye_center_x=eye_center_x,
        eye_center_y=eye_center_y,
        chin_y=chin_y,
        head_top_y=head_top_y,
        head_height=head_height,
        face_width=float(w),
        confidence=0.6,
    )
