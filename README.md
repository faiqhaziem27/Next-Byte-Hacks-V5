# Hado101

## Run on another laptop

Each laptop that runs the app needs Python, Ollama, and the local AI model.

### 1. Install prerequisites

Install:

- Python 3.10 or newer: <https://www.python.org/downloads/>
- Ollama for Windows/macOS/Linux: <https://ollama.com/download>

After installing Ollama, make sure it is running, then download the model used
by `parser.py`:

```powershell
ollama pull qwen3.5:4b
```

### 2. Get the project

Clone the repository and enter its folder:

```powershell
git clone https://github.com/faiqhaziem27/Next-Byte-Hacks-V5.git
cd Next-Byte-Hacks-V5
```

If the project is supplied as a ZIP file, extract it and run the commands from
the extracted project folder instead.

### 3. Install Python packages

```powershell
py -m pip install -r requirements.txt
```

On systems where `py` is unavailable, use:

```powershell
python -m pip install -r requirements.txt
```

### 4. Create the sample menu

Run this once if the laptop needs the sample menu and sample orders:

```powershell
py seed_data.py
```

This resets the local `stall.db` database. Do not run it again if the laptop
already contains orders that should be kept.

### 5. Start the app

```powershell
py app.py
```

Open <http://127.0.0.1:5000> in the same laptop's browser.

### Troubleshooting

- If Ollama reports that `qwen3.5:4b` is missing, run
  `ollama pull qwen3.5:4b`.
- If `ModuleNotFoundError` appears, run
  `py -m pip install -r requirements.txt`.
- Stop Flask with `Ctrl+C`.