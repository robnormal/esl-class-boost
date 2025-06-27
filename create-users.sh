if [ -z "$1" ]; then
  echo "Usage: create-users.sh <username>"
  exit 1
fi

if [ -z "$COGNITO_USER_POOL_ID" ]; then
  echo "Error: required environment variable 'COGNITO_USER_POOL_ID' not set"
  exit 1
fi

function random_string {
  tr -dc "A-Za-z\!-@" </dev/urandom | head -c "$1"
}

aws cognito-idp admin-create-user \
  --user-pool-id "$COGNITO_USER_POOL_ID" \
  --username "$1" \
  --message-action SUPPRESS

aws cognito-idp admin-update-user-attributes \
  --user-pool-id "$COGNITO_USER_POOL_ID" \
  --username "$1" \
  --user-attributes Name=email,Value="$1@example.com"

aws cognito-idp admin-update-user-attributes \
  --user-pool-id "$COGNITO_USER_POOL_ID" \
  --username "$1" \
  --user-attributes Name=email_verified,Value=true

PASSWORD=$(random_string 16)

aws cognito-idp admin-set-user-password \
  --user-pool-id "$COGNITO_USER_POOL_ID" \
  --username "$1" \
  --password "$PASSWORD" \
  --permanent

echo "Finished! User's password is:"
echo $PASSWORD
