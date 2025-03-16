## 1. System Components
### A. Web Application (Flask)
- Accepts text input via pasting, URLs, or file uploads.
- Provides authentication and user management.
- Displays processed results (summaries, vocabulary extractions).
- Polls for job completion instead of using response queues.

### B. Asynchronous Processing (AWS SQS & Workers)
- Uses SQS for work queues:
    - `vocab-work-queue` → Vocabulary extraction jobs.
    - `summarizer-work-queue` → Summarization jobs.
- Workers (running on EC2, Fargate, or Lambda) pull from SQS and process tasks.

### C. Storage
- S3 for text storage:
    - `uploads/` → Stores raw input files.
    - `processed/` → Stores generated summaries and vocab lists.
- RDS (PostgreSQL or MySQL) for metadata:
    - Tracks submissions, job statuses, and user preferences.

### D. Security & Access Controls
- IAM Roles grant secure, least-privilege access to S3.
- Bucket policies enforce HTTPS and restrict access to known services.
- Presigned URLs allow users to download files securely.

### E. Monitoring & Logging
- CloudWatch tracks worker processing times, errors, and queue activity.
- Structured logs (in RDS or CloudWatch) track API failures.

---

## 2. Processing Flow
### A. Document Submission
1. User uploads text via web app.
2. File is stored in S3 (`uploads/`).
3. A job message is sent to SQS (vocab/summarizer queues).
4. RDS entry is created (`status = pending`).

### B. Background Processing
5. Worker polls SQS, retrieves the job.
6. Worker processes text (extract vocab, summarize).
7. Processed results are stored in S3 (`processed/`).
8. RDS entry is updated (`status = completed`).

### C. Web App Polling for Results
9. User polls API → API checks RDS for job status.
10. If complete, API returns presigned URLs for downloading processed files.

---

## 3. Why This Design?
✅ Scalability → S3 + SQS + Worker Pool scales seamlessly.  
✅ Security → IAM roles, S3 bucket policies, presigned URLs.  
✅ Cost-Efficient → S3 + SQS eliminates need for always-on servers.  
✅ AWS Native → Fully integrates with AWS services.

---

This is a robust and production-ready design. Let me know if you’d like any refinements! 🚀
