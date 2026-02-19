# ---- Stage 1: Build Frontend ----
FROM node:20-slim AS frontend-build

WORKDIR /app

# Install dependencies
COPY front/package.json front/package-lock.json ./
RUN npm install

# Copy frontend source and build
COPY front/ .
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN npm run build

# ---- Stage 2: Open WebUI Backend ----
FROM python:3.11-slim

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Install Python dependencies
COPY front/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Open WebUI backend
COPY front/backend/ .

# Copy built frontend to /app/build (where FRONTEND_BUILD_DIR expects it)
# env.py: BASE_DIR = BACKEND_DIR.parent = /app
# env.py: FRONTEND_BUILD_DIR = BASE_DIR / "build" = /app/build
COPY --from=frontend-build /app/build /app/build

# Make start.sh executable
RUN chmod +x start.sh

# Cloud Run sets $PORT (default 8080)
ENV PORT=8080
ENV ENV=prod
ENV WEBUI_AUTH=false

EXPOSE 8080

CMD ["bash", "start.sh"]
