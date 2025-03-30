import json
import boto3
import os
import urllib.parse

from paragraph_extractor import TextExtractor

# Initialize AWS clients
s3_client = boto3.client('s3')

# Get environment variables
TARGET_BUCKET = os.environ.get('TARGET_BUCKET', 'rhr79-history-learning-paragraphs')
# Lambda's temp directory
TMP_DIR = '/tmp'

def handler(event, context):
    """
    Lambda function that encodes files uploaded to S3 as base64 and uploads to another bucket.

    Args:
        event (dict): The S3 event notification
        context (LambdaContext): Lambda context object

    Returns:
        dict: Response indicating success or failure
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        source_bucket = event['Records'][0]['s3']['bucket']['name']
        # The key comes URL-encoded, so we need to decode it
        source_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
        print(f"Processing file: {source_key} from bucket: {source_bucket}")

        key_parts = source_key.split('/')
        if len(key_parts) != 2:
            raise ValueError(f"Invalid file path: {source_key}; expected username/filename")

        username, local_filename = key_parts[0], key_parts[1]

        # Create file paths for local processing
        local_filename = os.path.basename(local_filename)
        local_filepath = os.path.join(TMP_DIR, local_filename)
        tmp_stats = os.statvfs(TMP_DIR)
        available_space = tmp_stats.f_frsize * tmp_stats.f_bavail
        print(f"Available space in /tmp: {available_space / (1024 * 1024):.2f} MB")
        print(f"Downloading file to: {local_filepath}")
        s3_client.download_file(source_bucket, source_key, local_filepath)

        file_size = os.path.getsize(local_filepath)
        print(f"Downloaded file size: {file_size / 1024:.2f} KB")
        paragraphs = TextExtractor(local_filepath).extract()
        target_key = source_key # Use same key in the new bucket

        s3_client.put_object(
            Bucket=TARGET_BUCKET,
            Key=target_key,
            Body=paragraphs.join("\n"),
            ContentType='application/octet-stream',
            Metadata={
                'original-bucket': source_bucket,
                'original-key': source_key,
                'encoding': 'base64'
            }
        )

        try:
            os.remove(local_filepath)
            print("Cleaned up local temporary files")
        except Exception as cleanup_error:
            print(f"Warning: Could not clean up temporary files: {str(cleanup_error)}")

        print(f"Successfully encoded and uploaded to {TARGET_BUCKET}/{target_key}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'File encoded and uploaded successfully',
                'source': f"{source_bucket}/{source_key}",
                'destination': f"{TARGET_BUCKET}/{target_key}"
            })
        }

    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f"Error processing file: {str(e)}"
            })
        }
