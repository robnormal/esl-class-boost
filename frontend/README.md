# English Vocabulary Tool – Frontend

This directory contains the React-based frontend for the English Vocabulary Tool. The frontend provides a user interface for interacting with the application's features, such as submitting documents, viewing extracted vocabulary, and managing summaries.

## Overview

The frontend is built with [React](https://reactjs.org/) and uses TypeScript for type safety. It communicates with backend services via API calls and provides a modern, responsive UI for end users.

## Directory Structure

- **public/**  
  Static assets such as the favicon, manifest, and images used by the app.

- **src/**  
  Main source code for the React application:
  - `App.tsx` – Main application component and routing.
  - `Dashboard.tsx` – Dashboard view for users.
  - `SubmissionForm.tsx` – Form for submitting documents for vocabulary extraction.
  - `SubmissionsList.tsx` – Displays a list of user submissions.
  - `SubmissionDetails.tsx` – Shows details for a specific submission.
  - `utils/auth.ts` – Authentication utilities (e.g., token handling).
  - `index.tsx` – Entry point for the React app.
  - `index.css`, `App.css` – Global and component-specific styles.

- **build.sh**  
  Script to build the frontend for production deployment.

- **package.json** and **package-lock.json**  
  Project dependencies and scripts.

- **tsconfig.json**  
  TypeScript configuration.

- **vite.config.js**  
  Configuration for the Vite build tool.

## Key Features

- **Document Submission:** Users can upload documents for vocabulary extraction.
- **Vocabulary & Summaries:** View extracted vocabulary words and generated summaries.
- **Authentication:** Handles user authentication (see `utils/auth.ts`).
- **Responsive UI:** Built with modern React best practices.

## Development

To get started with local development:

```bash
cd frontend
npm install
npm run dev
```

This will start the development server (using Vite) and open the app in your browser.

## Building for Production

To build the app for production:

```bash
npm run build
```

The output will be in the `dist/` directory, ready for deployment.

## Testing

Basic tests are included (see `App.test.js`). Run tests with:

```bash
npm test
```

## Notes

- The frontend expects backend services to be running and accessible via configured API endpoints.
- For environment-specific configuration, see `.env` files or Vite config.

---

For more details on the overall project, see the root-level `README.md`.
