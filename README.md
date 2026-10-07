# CIFAKE Image Detector

A simple CNN-based project for classifying an image as REAL or AI-GENERATED using the CIFAKE dataset. The project also shows a Grad-CAM heatmap and includes a confidence warning as an extra feature.

## Main features

- Binary REAL / FAKE image classification
- Simple CNN model based on the architecture style described in the CIFAKE paper
- Grad-CAM visual explanation
- Confidence warning: results below 70% confidence are marked **UNCERTAIN**
- Small Streamlit interface

## Project files

- `train.py` - trains the CNN and saves the model
- `evaluate.py` - evaluates the trained model
- `gradcam.py` - creates the Grad-CAM heatmap
- `utils.py` - preprocessing and confidence logic
- `app.py` - Streamlit application
- `data/README.txt` - dataset arrangement

## Run

See [RUN_POWERSHELL.md](RUN_POWERSHELL.md) for complete Windows PowerShell
commands. The included trained model means the app can be started directly
after installing dependencies.

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
python train.py
python evaluate.py
streamlit run app.py
```

Training defaults to 10 epochs with early stopping. For a quick one-epoch
smoke run, set `CIFAKE_EPOCHS=1` before running `train.py` (PowerShell:
`$env:CIFAKE_EPOCHS=1`).

## Added feature

The original CIFAKE work gives a binary prediction and Grad-CAM explanation. This project adds a small confidence-based warning. When the model confidence is below 70%, the application displays **UNCERTAIN** instead of presenting the prediction as a strong decision. This is intended to reduce overconfident use of a model on unclear inputs.

## Dataset

The supplied dataset contains 60,000 real CIFAR-10 images and 60,000 synthetic images generated using Stable Diffusion 1.4. The extracted training and test splits are included under `data/cifake/`.
