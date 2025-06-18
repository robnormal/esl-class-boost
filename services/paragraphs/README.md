# Paragraphs Service

This service processes text submissions and generates learning paragraphs using AWS services (SQS, S3, DynamoDB) for queue management and storage.

## Prerequisites

- Python 3.12 or higher
- Docker (for running LocalStack)
- AWS CLI (optional, for testing AWS services)

## Local Development Setup

### 1. Start LocalStack

First, start LocalStack to emulate AWS services locally:

```bash
docker run --rm -it \
  -p 4566:4566 \
  -p 4571:4571 \
  -e SERVICES=sqs,s3,dynamodb \
  -e DEFAULT_REGION=us-east-2 \
  -e AWS_ACCESS_KEY_ID=test \
  -e AWS_SECRET_ACCESS_KEY=test \
  localstack/localstack
```

### 2. Set Up Environment Variables

Create a `.env` file in the service directory with the following variables:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=us-east-2
AWS_ENDPOINT_URL=http://localhost:4566

# Service Configuration
IS_LOCAL=true
SUBMISSIONS_BUCKET=rhr79-history-learning-submissions
PARAGRAPHS_BUCKET=rhr79-history-learning-paragraphs
```

### 4. Run the Service

You can run the service in two ways:

#### Native

```bash
pip install -r requirements.txt
python main.py
```

#### Docker

Build the container:

```bash
# For production build
pip-compile
docker build -t paragraphs-service .

# For local development with LocalStack
pip-compile requirements.in ../../requirements-dev.in --output-file=requirements-dev.txt
docker build -t paragraphs-service --build-arg REQUIREMENTS_FILE=requirements-dev.txt .
```

Run the container:
```bash
docker run -d --env-file .env --name paragraphs-service paragraphs-service
```

## Testing LocalStack Integration

To verify that LocalStack is working correctly, you can use the following AWS CLI commands:

```bash
# Configure AWS CLI for LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-2

# Create the SQS queue
aws --endpoint-url=http://localhost:4566 sqs create-queue \
  --queue-name history-learning-paragraphs

# Create S3 buckets
aws --endpoint-url=http://localhost:4566 s3 mb s3://rhr79-history-learning-submissions
aws --endpoint-url=http://localhost:4566 s3 mb s3://rhr79-history-learning-paragraphs

# List queues to verify
aws --endpoint-url=http://localhost:4566 sqs list-queues

# List buckets to verify
aws --endpoint-url=http://localhost:4566 s3 ls
```

## Troubleshooting

1. **Connection Issues**
   - Ensure LocalStack is running (`docker ps` to check)
   - Verify the endpoint URL is correct
   - Check if port 4566 is accessible

2. **Authentication Errors**
   - Confirm you're using the test credentials
   - Verify environment variables are set correctly

3. **Queue/Bucket Not Found**
   - Make sure you've created the queue and buckets in LocalStack
   - Check the queue/bucket names match your configuration

## Development Notes

- The service uses the singleton pattern for AWS clients
- LocalStack endpoints are automatically detected when `IS_LOCAL=true`
- All AWS operations are logged for debugging purposes
- The service runs as a non-root user in Docker for security

## Additional Resources

- [LocalStack Documentation](https://docs.localstack.cloud/overview/)
- [AWS SQS Documentation](https://docs.aws.amazon.com/sqs/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/) 
