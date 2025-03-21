if [ -z "$1" ]; then
  echo "Usage: create-users.sh <username>"
  exit 1
fi

if [ -z "$COGNITO_USER_POOL_ID" ]; then
  echo "Error: required environment variable 'COGNITO_USER_POOL_ID' not set"
  exit 1
fi

aws cognito-idp admin-create-user \
  --user-pool-id "$COGNITO_USER_POOL_ID" \
  --username "$1" \
  --message-action SUPPRESS
