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
        # Log the event for debugging
        print(f"Received event: {json.dumps(event)}")

        # Get the source bucket and key from the event
        source_bucket = event['Records'][0]['s3']['bucket']['name']
        # The key comes URL-encoded, so we need to decode it
        source_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

        print(f"Processing file: {source_key} from bucket: {source_bucket}")

        # Create file paths for local processing
        local_filename = os.path.basename(source_key)
        local_filepath = os.path.join(TMP_DIR, local_filename)

        # Check available space in /tmp
        tmp_stats = os.statvfs(TMP_DIR)
        available_space = tmp_stats.f_frsize * tmp_stats.f_bavail
        print(f"Available space in /tmp: {available_space / (1024 * 1024):.2f} MB")

        # Download the file from S3 to local filesystem
        print(f"Downloading file to: {local_filepath}")
        s3_client.download_file(source_bucket, source_key, local_filepath)

        # Get file size for logging
        file_size = os.path.getsize(local_filepath)
        print(f"Downloaded file size: {file_size / 1024:.2f} KB")

        # Base64 encode the file and save locally
        paragraphs = TextExtractor(local_filepath).extract()

        # Generate the target key - maintaining the same path structure
        target_key = f"encoded/{source_key}.b64"

        # Upload the encoded file to the target bucket
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

        # Clean up local files
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
