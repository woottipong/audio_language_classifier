# ============================================================
# Audio Language Classifier — Docker Image
# Supports both GPU (NVIDIA CUDA) and CPU-only execution.
#
# Build:
#   GPU:  docker build -t audio-classifier .
#   CPU:  docker build --build-arg BASE_IMAGE=python:3.11-slim -t audio-classifier .
#
# Run:
#   docker run --rm -v ./audio_files:/app/audio_files -v ./results:/app/results audio-classifier
# ============================================================

ARG BASE_IMAGE=nvidia/cuda:12.1.1-runtime-ubuntu22.04

FROM ${BASE_IMAGE}

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install Python, ffmpeg, and essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Symlink python -> python3 if needed
RUN ln -sf /usr/bin/python3 /usr/bin/python

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY constants.py exceptions.py config.py utils.py ./
COPY classifier.py google_stt.py cache.py performance.py exporter.py main.py ./
COPY storage/ ./storage/

# Default command
ENTRYPOINT ["python", "main.py"]
CMD ["--input", "/app/audio_files", "--output", "/app/results"]
