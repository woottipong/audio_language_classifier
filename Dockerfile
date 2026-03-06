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

# Install Python 3.11, ffmpeg, and essentials
# Ubuntu 22.04 ships Python 3.10 by default — deadsnakes PPA provides 3.11
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-distutils \
    python3.11-venv \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.11
RUN python3.11 -m ensurepip --upgrade || (curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11)

# Symlink python/python3/pip to 3.11
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 \
 && ln -sf /usr/bin/python3.11 /usr/bin/python \
 && ln -sf /usr/local/bin/pip3.11 /usr/bin/pip || true

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY constants.py exceptions.py config.py utils.py ./
COPY classifier.py google_stt.py cache.py performance.py exporter.py main.py ./
COPY storage/ ./storage/

# Default command
ENTRYPOINT ["python", "main.py"]
CMD ["--input", "/app/audio_files", "--output", "/app/results"]
