#!/bin/bash

# Create S3 bucket
aws --endpoint-url=http://localhost:4566 s3 mb s3://rhr79-history-learning-submissions

# Configure CORS for the bucket
aws --endpoint-url=http://localhost:4566 s3api put-bucket-cors --bucket rhr79-history-learning-submissions --cors-configuration '{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"]
    }
  ]
}'

# Create the SQS queue
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name history-learning-paragraphs
