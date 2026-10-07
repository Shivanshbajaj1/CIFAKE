from __future__ import annotations

from pathlib import Path

import streamlit as st
import tensorflow as tf
from PIL import Image

from gradcam import make_gradcam, overlay_heatmap
from utils import find_model, prediction_text, preprocess_image

st.set_page_config(page_title="CIFAKE Detector", page_icon="I", layout="centered")
st.title("CIFAKE Image Detector")
st.write("Upload a small image to classify it as REAL or AI-GENERATED.")

try:
    model_path = find_model()
    model = tf.keras.models.load_model(model_path)
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

uploaded = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg"])

if uploaded:
    image = Image.open(uploaded).convert("RGB")
    st.image(image, caption="Input image", use_container_width=True)

    batch = preprocess_image(image)
    prob_real = float(model.predict(batch, verbose=0)[0][0])
    label, confidence, status = prediction_text(prob_real)

    if status == "UNCERTAIN":
        st.warning(f"Result: {label} | confidence: {confidence:.1%} | UNCERTAIN")
        st.caption("The model is not confident enough to give a strong result.")
    else:
        st.success(f"Result: {label} | confidence: {confidence:.1%}")

    st.subheader("Model explanation")
    heatmap = make_gradcam(model, batch, layer_name="conv2")
    st.image(overlay_heatmap(image, heatmap), caption="Grad-CAM heatmap", use_container_width=True)
