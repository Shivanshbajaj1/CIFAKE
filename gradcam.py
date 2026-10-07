from __future__ import annotations

import numpy as np
import tensorflow as tf
from PIL import Image


def make_gradcam(model: tf.keras.Model, image_batch: np.ndarray, layer_name: str = "conv2") -> np.ndarray:
    target_layer = model.get_layer(layer_name)
    feature_model = tf.keras.models.Model(model.inputs, target_layer.output)

    # Run the layers after the target convolution separately. This lets the
    # tape watch the convolution activations before calculating class scores,
    # which is required by current Keras 3 models for non-None gradients.
    head_input = tf.keras.Input(shape=target_layer.output.shape[1:])
    head_output = head_input
    target_index = model.layers.index(target_layer)
    for layer in model.layers[target_index + 1 :]:
        head_output = layer(head_output)
    classifier_head = tf.keras.Model(head_input, head_output)

    conv_outputs = feature_model([image_batch], training=False)

    with tf.GradientTape() as tape:
        tape.watch(conv_outputs)
        predictions = classifier_head(conv_outputs, training=False)
        # Explain the class selected by the model, whether REAL or FAKE.
        prob_real = predictions[:, 0]
        score = tf.where(prob_real >= 0.5, prob_real, 1.0 - prob_real)

    grads = tape.gradient(score, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(1, 2))
    conv_outputs = conv_outputs[0]
    pooled_grads = pooled_grads[0]

    heatmap = tf.reduce_sum(conv_outputs * pooled_grads, axis=-1)
    heatmap = tf.maximum(heatmap, 0)
    max_value = tf.reduce_max(heatmap)
    heatmap = heatmap / (max_value + 1e-8)
    return heatmap.numpy()


def overlay_heatmap(image: Image.Image, heatmap: np.ndarray, alpha: float = 0.45) -> Image.Image:
    from matplotlib import colormaps

    colors = colormaps["jet"](np.clip(heatmap, 0.0, 1.0))[..., :3]
    heatmap_img = Image.fromarray(np.uint8(colors * 255)).resize(image.size)
    base = image.convert("RGB")
    return Image.blend(base, heatmap_img, alpha=alpha)
