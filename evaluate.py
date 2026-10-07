from __future__ import annotations

import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from pathlib import Path

IMG_SIZE = (32, 32)
DATA_DIR = Path("data/cifake")
MODEL_PATH = Path("models/cifake_cnn.h5")


def main() -> None:
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Train the model first with python train.py")

    ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR / "test",
        labels="inferred",
        label_mode="binary",
        image_size=IMG_SIZE,
        batch_size=64,
        shuffle=False,
    )
    ds = ds.map(
        lambda images, labels: (tf.cast(images, tf.float32) / 255.0, labels),
        num_parallel_calls=tf.data.AUTOTUNE,
    )
    model = tf.keras.models.load_model(MODEL_PATH)

    y_true = []
    y_prob = []
    for x, y in ds:
        y_true.extend(y.numpy().astype(int).ravel().tolist())
        y_prob.extend(model.predict(x, verbose=0).ravel().tolist())

    y_pred = (np.array(y_prob) >= 0.5).astype(int)
    print("Accuracy:", accuracy_score(y_true, y_pred))
    print("Confusion matrix:\n", confusion_matrix(y_true, y_pred))
    print(classification_report(y_true, y_pred, target_names=["FAKE", "REAL"]))


if __name__ == "__main__":
    main()
