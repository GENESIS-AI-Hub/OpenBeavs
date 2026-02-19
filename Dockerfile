# ---- Stage 1: Build Frontend ----
FROM node:20-slim AS frontend-build

WORKDIR /app/front

# Install dependencies
COPY front/package.json front/package-lock.json ./
RUN npm install

# Copy frontend source and build
COPY front/ .
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN npm run build

# ---- Stage 2: Backend + Frontend ----
FROM python:3.9-slim

WORKDIR /app

# Install Python dependencies
COPY back/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY back/ .

# Copy built frontend into backend's 'frontend' directory
COPY --from=frontend-build /app/front/build ./frontend

# Cloud Run sets $PORT automatically
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
