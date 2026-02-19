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

WORKDIR /app/backend

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY front/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Open WebUI backend
COPY front/backend/ .

# Copy built frontend into backend/static (where Open WebUI expects it)
COPY --from=frontend-build /app/build ./static

# Make start.sh executable
RUN chmod +x start.sh

# Cloud Run sets $PORT (default 8080)
ENV PORT=8080
ENV ENV=prod

CMD ["bash", "start.sh"]
