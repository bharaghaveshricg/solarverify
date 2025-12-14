# -------------------------------
# SolarVerify – Inference Pipeline
# -------------------------------

FROM python:3.10-slim

# Prevent Python from buffering logs
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Default command
CMD ["python", "pipeline.py", "--csv", "input_sites.csv"]
