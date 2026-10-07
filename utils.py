from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image

IMG_SIZE = (32, 32)
CONFIDENCE_THRESHOLD = 0.70


def load_image(path_or_file) -> Image.Image:
    return Image.open(path_or_file).convert("RGB")


def preprocess_image(image: Image.Image) -> np.ndarray:
    image = image.resize(IMG_SIZE)
    arr = np.asarray(image, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def prediction_text(prob_real: float) -> Tuple[str, float, str]:
    prob_real = float(prob_real)
    prob_fake = 1.0 - prob_real
    label = "REAL" if prob_real >= 0.5 else "FAKE"
    confidence = max(prob_real, prob_fake)
    status = "CONFIDENT" if confidence >= CONFIDENCE_THRESHOLD else "UNCERTAIN"
    return label, confidence, status


def find_model(model_dir: str = "models") -> Path:
    candidates = [
        Path(model_dir) / "cifake_cnn.keras",
        Path(model_dir) / "cifake_cnn.h5",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "No trained model found. Run train.py first and keep the model in models/."
    )
