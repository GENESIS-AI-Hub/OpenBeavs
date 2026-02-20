# ---- Stage 1: Build Frontend & Copy to Backend ----
# Mirrors: cd front && npm run build:copy
FROM node:20-slim AS frontend-build

WORKDIR /app/front

# Install dependencies (cached unless package.json changes)
COPY front/package.json front/package-lock.json ./
RUN npm install

# Copy all frontend source (including backend/ and scripts/)
COPY front/ .

# Build and copy to backend/static (same as local dev)
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN npm run build:copy

# ---- Stage 2: Open WebUI Backend ----
# Single stage for Python to avoid missing C runtime library issues
FROM python:3.11-slim

# Install ALL system deps: build-time AND runtime
# (opencv, onnxruntime, soundfile, etc. need runtime C libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev curl libglib2.0-0 libsm6 libxext6 libxrender-dev \
    libsndfile1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Install Python dependencies (cached unless requirements.txt changes)
COPY front/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source + migrations (needed for DB init at startup)
COPY front/backend/open_webui ./open_webui

# Copy built frontend from Stage 1
COPY --from=frontend-build /app/front/backend/static ./static

# Copy package.json so env.py can read the app version
COPY front/package.json /app/package.json

# Copy CHANGELOG.md — env.py reads it from two locations:
# 1. Direct path at /app/CHANGELOG.md
# 2. Via pkgutil.get_data("open_webui", ...) → /app/backend/open_webui/CHANGELOG.md
COPY front/CHANGELOG.md /app/CHANGELOG.md
COPY front/CHANGELOG.md /app/backend/open_webui/CHANGELOG.md

# Create writable data directory for SQLite DB and migrations
RUN mkdir -p /app/backend/data

# --- Environment ---
# Tell Open WebUI where the frontend build lives
ENV FRONTEND_BUILD_DIR=/app/backend/static

# Secret key (avoids start.sh blocking on /dev/random)
ENV WEBUI_SECRET_KEY=cloud-run-secret-key-change-me

# Prevent HuggingFace model downloads at startup (would timeout)
ENV OFFLINE_MODE=true
ENV RAG_EMBEDDING_MODEL_AUTO_UPDATE=false
ENV RAG_RERANKING_MODEL_AUTO_UPDATE=false

# Cloud Run config
ENV PORT=8080
ENV HOST=0.0.0.0
ENV ENV=prod

EXPOSE 8080

# Run uvicorn directly (bypass start.sh to avoid /dev/random and extra logic)
CMD ["uvicorn", "open_webui.main:app", "--host", "0.0.0.0", "--port", "8080", "--forwarded-allow-ips", "*"]
