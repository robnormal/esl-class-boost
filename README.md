# ESL Class Boost

## Project Overview and Purpose

ESL Class Boost is a web application designed to help students who are attending college and learning
to speak English at the same time. It aims to help them improve their English vocabulary and
understand their assigned reading material at the same time. Users can submit documents via upload,
URL, or copy-paste, and the app automatically generates, for each paragraph, a one-sentence
summary and a list of vocabulary words with their definitions.

## Features

- Supports PDF, DOCX, HTML, Markdown, and image uploads; links to online files, and pasted text
- User authentication via AWS Cognito
- Per-paragraph summary and vocabulary list
- Click a word to see the definition
- Responsive UI - works on desktop and mobile devices

## Screenshots

> **Note:** Replace these descriptions with actual images or GIFs.

1. **Login Screen:**  
   _Shows the login form with branding and a sign-in button._

2. **Submission Form:**  
   _Displays the form for pasting text, entering a URL, or uploading a file. Drag-and-drop area is visible._

3. **Processing State:**  
   _Shows a loading spinner or animation while a submission is being processed._

4. **Results View:**  
   _Displays a processed document: each paragraph with its summary, vocabulary list, and marking options. Shows the slider for adjusting the common-word threshold._

5. **Submissions List:**  
   _Shows a list of recent submissions, with options to view details or rename entries._

6. **Mobile View:**  
   _Demonstrates the responsive design on a mobile device._

## Quick Start Guide

### Prerequisites

- Python 3.8+ and [Poetry](https://python-poetry.org/)
- Node.js 18+ and npm
- Docker (for local AWS emulation)
- AWS CLI (for deployment)
- (Optional) Google Cloud credentials for OCR

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd esl-class-boost
   ```

2. **Set up environment variables:**
   - In each service, copy example `.env.EXAMPLE` files to `.env` and edit.
   - See the `paragraphs` service for instructions on setting up Google Cloud.
   - **Google Cloud credentials:**  
     1. Go to the [Google Cloud Console](https://console.cloud.google.com/), create or select a project, and generate a service account key (JSON format) with the required permissions.
     2. Save the downloaded JSON file (e.g., `gcloud-creds.json`) in a secure location on your machine.
     3. Set the environment variable `GOOGLE_CLOUD_CREDENTIALS` to the path of this file. For example:
        ```bash
        export GOOGLE_CLOUD_CREDENTIALS=/path/to/gcloud-creds.json
        ```
     4. Ensure this variable is set in your shell or included in your `.env` file before running the application.

3. **Start local infrastructure:**
   ```bash
   bash local_start.sh
   ```

4. **Start backend services:**
   ```bash
   services/start_service.sh api
   services/start_service.sh paragraphs
   services/start_service.sh vocabulary
   services/start_service.sh summaries
   ```

5. **Start the frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   The app will open at [http://localhost:3000](http://localhost:3000).

### Production Deployment

```bash
bash deploy_react.sh
```

See `docs/deployment-automation.md` for CI/CD and infrastructure details.

## How to Run Tests

### Frontend

```bash
cd frontend
npm test
```

### Backend (for each service)

```bash
cd services/<service-name>
poetry install
poetry run pytest tests/
```

Replace `<service-name>` with `api`, `paragraphs`, `summaries`, or `vocabulary`.

## Technologies Used

- **Frontend:**
  - React
  - TypeScript
  - Vite
  - AWS Amplify (for authentication)
  - React Testing Library, Vitest, Jest (for testing)

- **Backend:**
  - Python 3.8+
  - Poetry (dependency management)
  - Flask (API service)
  - Boto3 (AWS SDK)
  - OpenAI (summarization)
  - NLTK, wordfreq (NLP and vocabulary extraction)
  - Docker (containerization)
  - LocalStack (local AWS emulation)
  - Pytest, Black, Flake8, Mypy (testing and linting)

- **Infrastructure:**
  - Terraform (AWS infrastructure as code)
  - AWS (S3, DynamoDB, SQS, Cognito, ECS, CloudFront)
  - GitHub Actions (CI/CD)

## TODO

- Add user control for word difficulty threshold
- Allow users to mark/hide words they know
- Add a chat for users to ask questions about their documents
