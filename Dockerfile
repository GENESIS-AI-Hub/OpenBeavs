# ---- Stage 1: Build Frontend & Copy to Backend ----
# Mirrors: cd front && npm run build:copy
FROM node:20-slim AS frontend-build

WORKDIR /app/front

# Install dependencies
COPY front/package.json front/package-lock.json ./
RUN npm install

# Copy all frontend source (including backend/ and scripts/)
COPY front/ .

# Build and copy to backend/static (same as local dev)
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN npm run build:copy

# ---- Stage 2: Open WebUI Backend ----
# Mirrors: cd front/backend && sh start.sh
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Install Python dependencies
COPY front/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend (open_webui/, start.sh, etc.) from Stage 1
# This includes backend/static/ with the built frontend
COPY --from=frontend-build /app/front/backend/open_webui ./open_webui
COPY --from=frontend-build /app/front/backend/static ./static
COPY --from=frontend-build /app/front/backend/start.sh ./start.sh

# Copy package.json so env.py can read the version
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
