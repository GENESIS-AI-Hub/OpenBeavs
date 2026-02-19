# ---- Stage 1: Install Python deps (heaviest layer, cached aggressively) ----
FROM python:3.11-slim AS python-deps

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
COPY front/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: Build Frontend & Copy to Backend ----
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

# ---- Stage 3: Final Image ----
# Mirrors: cd front/backend && sh start.sh
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Copy pre-installed Python packages from Stage 1
COPY --from=python-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Copy backend source
COPY --from=frontend-build /app/front/backend/open_webui ./open_webui
COPY --from=frontend-build /app/front/backend/start.sh ./start.sh

# Copy built frontend (from build:copy)
COPY --from=frontend-build /app/front/backend/static ./static

# Copy package.json for version info
COPY front/package.json /app/package.json

# Create data directory
RUN mkdir -p /app/backend/data && chmod +x start.sh

# Tell Open WebUI where the frontend build is
ENV FRONTEND_BUILD_DIR=/app/backend/static

# Prevent model downloads at startup
ENV OFFLINE_MODE=true
ENV RAG_EMBEDDING_MODEL_AUTO_UPDATE=false
ENV RAG_RERANKING_MODEL_AUTO_UPDATE=false

# Cloud Run config
ENV PORT=8080
ENV ENV=prod

EXPOSE 8080

CMD ["bash", "start.sh"]
