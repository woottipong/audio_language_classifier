# CLAUDE.md - Audio Language Classifier

## Build and Run Commands
- **Setup Venv (first time)**: `python3.13 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- **Activate Venv**: `source .venv/bin/activate`
- **Install Dependencies**: `.venv/bin/pip install -r requirements.txt`
- **Run Basic Detection**: `.venv/bin/python main.py -i ./audio_files -o ./results`
- **Run with Transcription**: `.venv/bin/python main.py -i ./audio_files --transcribe`
- **Run with Google STT (Thai)**: `.venv/bin/python main.py -i ./audio_files --transcribe --use-google-for-thai`
- **GPU Run**: `.venv/bin/python main.py -i ./audio_files --transcribe --device cuda --compute-type float16`
- **Syntax Check**: `.venv/bin/python -m py_compile *.py`
- **Check GPU Support**: `python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"`

> **Note**: macOS ships Python 3.9 at `/usr/bin/python3` — always use the `.venv` (Python 3.13) to avoid Google SDK deprecation warnings.

## Development Guidelines
- **Type Safety**: Mandatory 100% type hint coverage. Use `from __future__ import annotations` with modern syntax (`list[str]`, `dict[str, float]`, `X | None`) — never `typing.List/Dict/Optional`.
- **Logging**: Use `%s` lazy formatting in all `logger.*()` calls — never f-strings (avoids unnecessary evaluation).
- **Error Handling**: Use custom exceptions from `exceptions.py` (base: `AudioClassifierError`). Avoid bare `except: pass`.
- **Configuration**: All settings must be defined in `config.py` (`AppConfig`) and validated via `config.validate()`.
- **Constants**: No magic numbers. Use `constants.py` for all defaults and model strings.
- **Concurrency**: Use `ThreadPoolExecutor` for batch processing; ensure the Whisper model singleton is thread-safe.
- **Code Style**: Follow PEP 8. Use descriptive names (e.g., `is_english` instead of `en_f`).
- **Imports**: Organize imports: `from __future__ import annotations` first, then standard library, third-party (alphabetical), then local modules.

## Architecture Context
- **Modular Design**: Entry point is `main.py`. Logic is split into `classifier.py` (Whisper), `google_stt.py` (Chirp 2), and `storage/` (File access).
- **Inference**: Uses `faster-whisper` (CTranslate2) for speed.
- **Storage**: Pluggable backend system via `storage/base.py`.
- **Caching**: Result caching in `cache.py` to optimize re-runs.
