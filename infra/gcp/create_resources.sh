#!/bin/bash
set -euo pipefail

# cd to script dir
cd "$(dirname "${BASH_SOURCE[0]}")"

PROJECT_ID=flash-spot-456815-c3
LOCATION=us
BUCKET_NAME=rhr79-history-learning-ocr
SA_NAME=docai-access
SA_EMAIL=$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com
KEY_FILE=key.json

# Enable required APIs
gcloud services enable documentai.googleapis.com storage.googleapis.com --project=$PROJECT_ID

# In the console, create a Document OCR processor called "Basic OCR", if it doesn't exist
# TODO: Add directions for using curl to do this

# Create bucket if it doesn't exist
if ! gsutil ls -p $PROJECT_ID | grep -q "gs://$BUCKET_NAME/"; then
  gcloud storage buckets create gs://$BUCKET_NAME \
    --location=$LOCATION \
    --uniform-bucket-level-access \
    --project=$PROJECT_ID
else
  echo "Bucket gs://$BUCKET_NAME already exists. Skipping creation."
fi

# Create service account if it doesn't exist
if ! gcloud iam service-accounts list --project=$PROJECT_ID \
    --format="value(email)" | grep -qx "$SA_EMAIL"; then
  gcloud iam service-accounts create $SA_NAME \
    --description="Access for Document AI processing" \
    --display-name="DocAI Access" \
    --project=$PROJECT_ID
else
  echo "Service account $SA_EMAIL already exists. Skipping creation."
fi

# Assign roles if not already assigned
for ROLE in roles/documentai.apiUser roles/storage.objectViewer; do
  if ! gcloud projects get-iam-policy "$PROJECT_ID" \
      --flatten="bindings[].members" \
      --format="table(bindings.role)" \
      --filter="bindings.members:serviceAccount:$SA_EMAIL AND bindings.role:$ROLE" \
      | grep -q "$ROLE"; then
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
      --member="serviceAccount:$SA_EMAIL" \
      --role="$ROLE"
  else
    echo "Role $ROLE already bound to $SA_EMAIL. Skipping."
  fi
done

# Create key if it doesn't exist
if [ ! -f "$KEY_FILE" ]; then
  gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL" \
    --project="$PROJECT_ID"
else
  echo "Key file $KEY_FILE already exists. Skipping key creation."
fi
