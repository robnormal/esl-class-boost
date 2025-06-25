# TODO: flesh out this README

To launch everything locally:

- install poetry
- install poetry dotenv
- add environment variables (to .env or .bashrc) (instructions, example file)
  - include instructions for getting gcloud credentials

```shell
bash local_start.sh
backend/start_service.sh api
backend/start_service.sh paragraphs
backend/start_service.sh vocabulary
backend/start_service.sh summaries
```

To put into production:

```shell
bash deploy-react.sh
```

To set secrets necessary for AWS:
```shell
aws ssm put-parameter --name "/learning-tool/aws_access_key_id" --type "SecureString" --value "<The actual key id>"
aws ssm put-parameter --name "/learning-tool/aws_secret_access_key" --type "SecureString" --value "<The actual access key>"
aws ssm put-parameter --name "/learning-tool/gcp_project_id" --type "SecureString" --value "<The actual Google project id>"
aws ssm put-parameter --name "/learning-tool/google_application_credentials" --type "SecureString" --value "<The actual creds>"
```
