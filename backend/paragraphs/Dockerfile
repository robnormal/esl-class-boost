FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PARAGRAPHS_QUEUE_URL="https://sqs.us-east-2.amazonaws.com/${AWS_ACCOUNT_ID}/history-learning-paragraphs-queue" \
    SUBMISSIONS_BUCKET="rhr79-history-learning-submissions" \
    PARAGRAPHS_BUCKET="rhr79-history-learning-paragraphs"

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service code
COPY . .

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Run the service
CMD ["python", "main.py"]
