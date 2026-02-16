# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY agent/requirements.txt .
COPY requirements.txt ./requirements-top.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-top.txt

# Install uvicorn for serving the A2A app
RUN pip install --no-cache-dir uvicorn[standard]

# Copy agent code
COPY agent/ ./agent/
COPY .env* ./

# Expose port 8081 (avoids conflicts with other agents on 8080)
EXPOSE 8081

# Run the A2A server
CMD ["uvicorn", "agent.agent:a2a_app", "--host", "0.0.0.0", "--port", "8081"]
