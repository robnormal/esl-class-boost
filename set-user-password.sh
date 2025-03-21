if [ -z "$COGNITO_USER_POOL_ID" ]; then
  echo "Error: required environment variable 'COGNITO_USER_POOL_ID' not set"
  exit 1
fi

if [ -z "$1" ]; then
  echo "Usage: create-users.sh <username> [password]"
  exit 1
fi

if [ -z "$2" ]; then
  read -r -p "Enter password: " pass
else
  pass="$2"
fi

aws cognito-idp admin-set-user-password \
  --user-pool-id "$COGNITO_USER_POOL_ID" \
  --username "$1" \
  --password "$pass" \
  --permanent
