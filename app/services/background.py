import mediapipe as mp
import numpy as np
from PIL import Image

_selfie_segmentation = mp.solutions.selfie_segmentation.SelfieSegmentation(
    model_selection=1,
)


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def replace_background(image: Image.Image, background_color: str) -> Image.Image:
    rgb = np.array(image.convert("RGB"))
    results = _selfie_segmentation.process(rgb)
    mask = results.segmentation_mask

    if mask is None:
        return image.convert("RGB")

    # Feather mask edges for a cleaner cutout.
    mask = np.clip(mask, 0.0, 1.0)
    mask = np.stack([mask, mask, mask], axis=-1)

    bg = np.array(_hex_to_rgb(background_color), dtype=np.float32)
    foreground = rgb.astype(np.float32)
    composited = foreground * mask + bg * (1.0 - mask)
    return Image.fromarray(np.uint8(np.clip(composited, 0, 255)))
