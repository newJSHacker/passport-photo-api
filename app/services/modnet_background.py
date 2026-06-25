"""
MODNet background removal (ported from digital/apps/home/utils/bgremove.py).

Uses the photographic portrait matting ONNX model with onnxruntime.
"""

from __future__ import annotations

import threading
from pathlib import Path

import cv2
import numpy as np
import onnxruntime
from PIL import Image

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_MODEL_PATH = _DATA_DIR / "modnet.onnx"

_engine: "ModnetBackgroundRemover | None" = None
_engine_lock = threading.Lock()


def modnet_model_available() -> bool:
    return _MODEL_PATH.is_file()


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


class ModnetBackgroundRemover:
    def __init__(self) -> None:
        if not modnet_model_available():
            raise FileNotFoundError(
                f"MODNet model not found at {_MODEL_PATH}. "
                "Run: python scripts/download_modnet.py"
            )

        self._session = onnxruntime.InferenceSession(
            str(_MODEL_PATH),
            providers=["CPUExecutionProvider"],
        )
        self._input_name = self._session.get_inputs()[0].name
        self._output_name = self._session.get_outputs()[0].name
        self._inference_lock = threading.Lock()

    @staticmethod
    def _get_scale_factor(im_h: int, im_w: int, ref_size: int) -> tuple[float, float]:
        if max(im_h, im_w) < ref_size or min(im_h, im_w) > ref_size:
            if im_w >= im_h:
                im_rh = ref_size
                im_rw = int(im_w / im_h * ref_size)
            else:
                im_rw = ref_size
                im_rh = int(im_h / im_w * ref_size)
        else:
            im_rh = im_h
            im_rw = im_w

        im_rw -= im_rw % 32
        im_rh -= im_rh % 32

        return im_rw / im_w, im_rh / im_h

    def _matting_mask(self, bgr: np.ndarray) -> np.ndarray:
        ref_size = 512
        im = bgr.copy()

        if len(im.shape) == 2:
            im = im[:, :, None]
        if im.shape[2] == 1:
            im = np.repeat(im, 3, axis=2)
        elif im.shape[2] == 4:
            im = im[:, :, 0:3]

        im = (im - 127.5) / 127.5
        im_h, im_w, _ = im.shape
        x_scale, y_scale = self._get_scale_factor(im_h, im_w, ref_size)
        im = cv2.resize(im, None, fx=x_scale, fy=y_scale, interpolation=cv2.INTER_AREA)

        im = np.transpose(im)
        im = np.swapaxes(im, 1, 2)
        im = np.expand_dims(im, axis=0).astype("float32")

        with self._inference_lock:
            result = self._session.run(
                [self._output_name],
                {self._input_name: im},
            )

        matte = (np.squeeze(result[0]) * 255).astype("uint8")
        return cv2.resize(matte, dsize=(im_w, im_h), interpolation=cv2.INTER_AREA)

    def remove_background(self, image: Image.Image, background_color: str) -> Image.Image:
        rgb = np.array(image.convert("RGB"))
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        mask = self._matting_mask(bgr)

        alpha = mask.astype(np.float32) / 255.0
        alpha = np.clip(alpha, 0.0, 1.0)
        alpha_3 = np.stack([alpha, alpha, alpha], axis=-1)

        bg = np.array(_hex_to_rgb(background_color), dtype=np.float32)
        foreground = rgb.astype(np.float32)
        composited = foreground * alpha_3 + bg * (1.0 - alpha_3)
        return Image.fromarray(np.uint8(np.clip(composited, 0, 255)))


def get_modnet_engine() -> ModnetBackgroundRemover:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = ModnetBackgroundRemover()
    return _engine


def replace_background_modnet(image: Image.Image, background_color: str) -> Image.Image:
    return get_modnet_engine().remove_background(image, background_color)
