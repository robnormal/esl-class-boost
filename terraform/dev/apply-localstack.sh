#!/bin/bash

# Stop on error
set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

# Delete terraform files except main.tf
find . -maxdepth 1 -type f -name '*.tf' ! -name 'main.tf' -delete

# Copy terraform files from parent
cp ../db.tf ../s3.tf ../sqs.tf .

terraform init
terraform apply
