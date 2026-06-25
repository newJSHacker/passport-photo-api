"""Download the MODNet ONNX model used for background removal."""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

MODEL_URL = (
    "https://github.com/Zeyi-Lin/HivisionIDPhotos/releases/download/"
    "pretrained-model/modnet_photographic_portrait_matting.onnx"
)
TARGET = Path(__file__).resolve().parents[1] / "app" / "data" / "modnet.onnx"


def main() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if TARGET.exists() and TARGET.stat().st_size > 20_000_000:
        print(f"Model already exists: {TARGET}")
        return

    print(f"Downloading MODNet model to {TARGET} ...")
    urllib.request.urlretrieve(MODEL_URL, TARGET)
    print(f"Done ({TARGET.stat().st_size // 1_000_000} MB)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"Download failed: {exc}", file=sys.stderr)
        sys.exit(1)
