import React, { useState } from 'react';

interface Props {
  userId: string;
}

type SetStatus = React.Dispatch<React.SetStateAction<string | null>>;

function setErrorStatus(setStatus: SetStatus, exception: Error) {
  console.error(exception);
  setStatus(`❌ Upload failed: ${exception.message}`);
}

function SubmissionForm({ userId }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file) {
      alert('Please select a file to upload.');
      return;
    }

    try {
      setStatus('Requesting upload URL...');

      const response = await fetch('/generate-upload-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          file_name: file.name,
          content_preview: file.name,
        }),
      });

      if (!response.ok) {
        return setErrorStatus(setStatus, new Error(`Failed to get upload URL: ${response.statusText}`))
      }

      const data = await response.json();
      const { upload_url, submission_id } = data;

      setStatus('Uploading to S3...');

      const uploadResult = await fetch(upload_url, {
        method: 'PUT',
        headers: {
          'Content-Type': 'text/plain',
        },
        body: file,
      });

      if (!uploadResult.ok) {
        return setErrorStatus(setStatus, new Error(`Upload to S3 failed: ${uploadResult.statusText}`));
      }

      setStatus(`✅ File uploaded successfully! Submission ID: ${submission_id}`);
    } catch (err: any) {
      setErrorStatus(setStatus, err);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h3>Upload a File</h3>
      <input
        type="file"
        accept=".txt"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button type="submit">Submit</button>
      {status && <p>{status}</p>}
    </form>
  );
}

export default SubmissionForm;
