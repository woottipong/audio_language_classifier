# ============================================================
# Audio Language Classifier — Docker Image
# Supports both GPU (NVIDIA CUDA) and CPU-only execution.
#
# Build:
#   GPU:  docker build -t audio-classifier .
#   CPU:  docker build --build-arg BASE_IMAGE=python:3.11-slim -t audio-classifier .
#   Bake model into image (no download on each run):
#         docker build --build-arg BAKE_MODEL=large-v3-turbo -t audio-classifier .
#
# Run (model cache persisted on host — recommended):
#   GPU:  docker run --rm --gpus all \
#           -v $(pwd)/model_cache:/root/.cache/huggingface \
#           -v $(pwd)/audio_files:/data/input \
#           -v $(pwd)/results:/data/output \
#           audio-classifier -i /data/input -o /data/output --device cuda --compute-type float16
# ============================================================

ARG BASE_IMAGE=nvidia/cuda:12.1.1-runtime-ubuntu22.04
# Set to a model name (e.g. large-v3-turbo) to bake the model into the image
ARG BAKE_MODEL=""

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

# Pre-download model into image (only when BAKE_MODEL is set)
ARG BAKE_MODEL=""
RUN if [ -n "$BAKE_MODEL" ]; then \
      python3.11 -c "from faster_whisper import WhisperModel; WhisperModel('$BAKE_MODEL', device='cpu', compute_type='int8')"; \
    fi

# Default command
ENTRYPOINT ["python", "main.py"]
CMD ["--input", "/app/audio_files", "--output", "/app/results"]
