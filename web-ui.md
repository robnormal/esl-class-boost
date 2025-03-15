### **Web Interface Overview for MVP**

#### **🔑 User Authentication**
- Users must **log in** before accessing the app.
- They can **log out** manually.

#### **📜 Text Submission**
- Users can **paste text**, **enter a URL**, or **upload a file** (`.txt`, `.pdf`, `.docx`, `.html`, `.md`, `.png/.jpg` for OCR).
- **Drag-and-drop** support for file uploads.
- Only **one submission at a time** (no batch uploads).
- If the submission **exceeds 200,000 characters or 100MB**, an **error message** will be shown.
- **Duplicate detection**: If the exact same text was submitted before, a **warning** appears but users can still proceed.

#### **⏳ Submission Processing**
- A **waiting animation** will be shown while processing.
- Users can **cancel a submission**, and already-processed data will be saved.
- Users can **resume canceled submissions** at any time.
- **Rate limit**: 10 submissions per minute (generic error if exceeded).

#### **📑 Processed Results Display**
- **Everything is expanded by default** (summaries + vocabulary).
- Each paragraph shows:
    - A **one-sentence summary**.
    - A **list of extracted uncommon words**.
    - The **first few words of the paragraph** as a reference.
- Words can be **individually marked** as:
    - ✅ Already known
    - 📖 Now learned
    - 🚫 Not interested
    - ⬜ Unmarked (default)
- Marking a word **changes its visual style**.
- Users can **adjust the common-word threshold** using a **slider with text input** and **re-run vocabulary extraction** for past submissions.

#### **📂 Managing Submissions**
- The homepage shows:
    - **Submission form at the top** (paste, URL, or file).
    - **Recent submissions list below**, sorted **newest first**.
    - A **"View All Submissions"** link for older entries.
- **Submissions are permanent** (no deleting).
- Users can **rename submissions** at any time.
- No auto-logout—users stay logged in indefinitely.

#### **⬇️ Exporting Results**
- Users can **download results as Markdown (`.md`)**.
- Results can be **viewed in HTML** in the browser.
