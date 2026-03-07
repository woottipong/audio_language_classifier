# Audio Language Classifier

ตรวจจับภาษาในไฟล์เสียง (ไทย / อังกฤษ) และถอดเนื้อหาเป็นข้อความ รองรับไฟล์จำนวนมากด้วย concurrent processing และ result caching

## Tech Stack

- **Language detection** — [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- **Thai transcription** — Google Cloud STT (Chirp 2) หรือ Whisper
- **Output** — CSV + JSON

## Requirements

- Python 3.10+
- ffmpeg

```bash
brew install ffmpeg          # macOS
sudo apt-get install ffmpeg  # Ubuntu
```

## Setup

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# ตรวจจับภาษา (ไม่ถอดเสียง)
python main.py -i ./audio_files -o ./results

# ตรวจจับภาษา + ถอดเสียง
python main.py -i ./audio_files -o ./results --transcribe

# ใช้ Google Chirp 2 สำหรับภาษาไทย (แม่นยำกว่า)
python main.py -i ./audio_files -o ./results --transcribe --use-google-for-thai

# เปิด cache (ข้ามไฟล์ที่ประมวลผลแล้ว)
python main.py -i ./audio_files -o ./results --enable-cache

# GPU (ถ้ามี CUDA)
python main.py -i ./audio_files -o ./results --device cuda --compute-type float16

# GPU + large-v3-turbo (เร็วกว่า large ~4x, accuracy ใกล้เคียง)
python main.py -i ./audio_files -o ./results --transcribe --device cuda --compute-type float16 --model-size large-v3-turbo
```

ผลลัพธ์จะอยู่ที่ `./results/summary.csv` และ `./results/summary.json`

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `-i, --input` | `./audio_files` | โฟลเดอร์ไฟล์เสียง |
| `-o, --output` | `./results` | โฟลเดอร์ output |
| `--model-size` | `base` | `tiny` / `base` / `small` / `medium` / `large` / `large-v3-turbo` / `turbo` |
| `--device` | `auto` | `auto` / `cpu` / `cuda` |
| `--compute-type` | `int8` | `int8` / `float16` / `float32` |
| `--max-workers` | `4` | จำนวน thread |
| `--transcribe` | off | ถอดเสียงเป็นข้อความ |
| `--use-google-for-thai` | off | ใช้ Google Chirp 2 สำหรับภาษาไทย |
| `--preprocess-audio` | off | ffmpeg highpass+loudnorm preprocessing สำหรับเสียงโทรศัพท์ที่มี noise |
| `--enable-cache` | off | cache ผลลัพธ์ (ข้ามไฟล์ที่ไม่เปลี่ยน) |
| `--log-level` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `--log-file` | — | บันทึก log ลงไฟล์ |

## Google Cloud STT Setup

สำหรับ `--use-google-for-thai`:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
# หรือใส่ไว้ใน .env
```

## Docker

```bash
# Build (standard)
docker build -t audio-classifier .

# Build — bake model into image (ไม่ต้อง download ทุกครั้งที่รัน)
docker build --build-arg BAKE_MODEL=large-v3-turbo -t audio-classifier .

# Run (CPU) — mount model cache เพื่อไม่ต้อง download ซ้ำ
docker run --rm \
  -v $(pwd)/model_cache:/root/.cache/huggingface \
  -v $(pwd)/audio_files:/data/input \
  -v $(pwd)/results:/data/output \
  audio-classifier -i /data/input -o /data/output

# Run (GPU)
docker run --rm --gpus all \
  -v $(pwd)/model_cache:/root/.cache/huggingface \
  -v $(pwd)/audio_files:/data/input \
  -v $(pwd)/results:/data/output \
  audio-classifier -i /data/input -o /data/output \
  --device cuda --compute-type float16 --model-size large-v3-turbo --transcribe
```

> **Model cache:** สร้าง folder `model_cache/` ไว้บน host ครั้งเดียว — Docker จะ reuse ได้ทุก run โดยไม่ต้อง download ซ้ำ

## Output Format

**summary.csv** (detection only)
```
file_name,detected_lang,probability,is_english,duration
interview_01.wav,th,0.97,False,45.2
interview_02.wav,en,0.99,True,30.0
```

**summary.csv** (with `--transcribe`)
```
file_name,detected_lang,probability,is_english,duration,transcription,transcription_source
interview_01.wav,th,0.97,False,45.2,สวัสดีครับ...,whisper
interview_02.wav,en,0.99,True,30.0,Hello how are you...,whisper
```

**summary.json** — รูปแบบเดียวกันทุก field

## Tests

```bash
.venv/bin/pytest tests/ -v
# 129 passed
```
