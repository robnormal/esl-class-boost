FROM python:3.12-slim

WORKDIR /app

# Add build argument for requirements file
ARG REQUIREMENTS_FILE=requirements.txt

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies using the specified requirements file
COPY ${REQUIREMENTS_FILE} requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service code
COPY . .

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Run the service
CMD ["python", "main.py"]
