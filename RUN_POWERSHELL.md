# Run on Windows PowerShell

The ZIP includes the dataset and the trained checkpoint. You can launch the app
without training again.

## 1. Extract the project

Run these commands in PowerShell:

```powershell
$zipPath = "$env:USERPROFILE\Downloads\newp\CIFAKE_Complete_Project.zip"
$projectPath = "$env:USERPROFILE\Downloads\CIFAKE_Project_Package"
Expand-Archive -LiteralPath $zipPath -DestinationPath $projectPath
Set-Location $projectPath
```

If you extract the ZIP to a different location, set `$projectPath` to that
folder and run `Set-Location $projectPath`.

## 2. Create the environment and install dependencies

Use 64-bit Python 3.12. If `python --version` does not show Python 3.12, install
Python 3.12 and enable **Add python.exe to PATH** in its installer.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

These commands do not require activating the virtual environment.

## 3. Start the app

The supplied trained model is loaded automatically by the app:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

Streamlit prints the local address to open in your browser. Upload a PNG or JPG
image to get a REAL/FAKE prediction, confidence indicator, and Grad-CAM view.

## Optional: retrain and evaluate

The project includes 100,000 training images and 20,000 test images. A full
training run defaults to 10 epochs with early stopping and replaces the saved
checkpoint when validation accuracy improves:

```powershell
.\.venv\Scripts\python.exe train.py
.\.venv\Scripts\python.exe evaluate.py
```

For a quicker one-epoch run, set the environment variable first:

```powershell
$env:CIFAKE_EPOCHS = "1"
.\.venv\Scripts\python.exe train.py
.\.venv\Scripts\python.exe evaluate.py
```

The supplied checkpoint was trained for one epoch. Its test results are
recorded in `RESULTS.md`.
