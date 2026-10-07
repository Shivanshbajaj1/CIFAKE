from __future__ import annotations

import os
from pathlib import Path

import tensorflow as tf

IMG_SIZE = (32, 32)
BATCH_SIZE = 64
EPOCHS = int(os.environ.get("CIFAKE_EPOCHS", "10"))
DATA_DIR = Path("data/cifake")
MODEL_DIR = Path("models")


def build_model() -> tf.keras.Model:
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(*IMG_SIZE, 3)),
        tf.keras.layers.Conv2D(32, (3, 3), activation="relu", name="conv1"),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Conv2D(32, (3, 3), activation="relu", name="conv2"),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=["accuracy", tf.keras.metrics.Precision(), tf.keras.metrics.Recall()],
    )
    return model


def main() -> None:
    train_dir = DATA_DIR / "train"
    test_dir = DATA_DIR / "test"
    if not train_dir.exists() or not test_dir.exists():
        raise FileNotFoundError(
            "Expected data/cifake/train and data/cifake/test. See data/README.txt."
        )

    train_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        labels="inferred",
        label_mode="binary",
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=True,
        seed=42,
        validation_split=0.10,
        subset="training",
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        labels="inferred",
        label_mode="binary",
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=True,
        seed=42,
        validation_split=0.10,
        subset="validation",
    )
    test_ds = tf.keras.utils.image_dataset_from_directory(
        test_dir,
        labels="inferred",
        label_mode="binary",
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    autotune = tf.data.AUTOTUNE
    normalize = lambda images, labels: (tf.cast(images, tf.float32) / 255.0, labels)
    train_ds = train_ds.map(normalize, num_parallel_calls=autotune)
    val_ds = val_ds.map(normalize, num_parallel_calls=autotune)
    test_ds = test_ds.map(normalize, num_parallel_calls=autotune)
    train_ds = train_ds.prefetch(autotune)
    val_ds = val_ds.prefetch(autotune)
    test_ds = test_ds.prefetch(autotune)

    model = build_model()
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        # HDF5 saves reliably with the TensorFlow 2.21 / Keras 3 Windows wheel.
        MODEL_DIR / "cifake_cnn.h5",
        monitor="val_accuracy",
        save_best_only=True,
        mode="max",
    )
    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor="val_accuracy", patience=3, restore_best_weights=True
    )

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=[checkpoint, early_stop],
    )

    results = model.evaluate(test_ds, return_dict=True)
    print("Test results:")
    for name, value in results.items():
        print(f"{name}: {value:.4f}")


if __name__ == "__main__":
    main()
