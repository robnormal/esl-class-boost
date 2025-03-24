import React, { useState } from 'react';
import { fetchAuthSession } from '@aws-amplify/auth';

interface Props {
  userId: string;
}

type SetStatus = React.Dispatch<React.SetStateAction<string | null>>;

const API_GATEWAY_URL = process.env.REACT_APP_API_GATEWAY_URL!;

async function getSessionToken(): Promise<string|undefined> {
  const session = await fetchAuthSession(); // From Amplify Auth
  return session.tokens?.idToken?.toString();
}

function setErrorStatus(setStatus: SetStatus, exception: Error) {
  console.error(exception);
  setStatus(`❌ Upload failed: ${exception.message}`);
}

async function hashFile(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
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
      setStatus('🔍 Hashing file...');
      const fileHash = await hashFile(file);

      const auth_token = await getSessionToken();
      if (!auth_token) {
        return setErrorStatus(setStatus, new Error('Not logged in'))
      }

      setStatus('🔗 Requesting upload URL...');
      const response = await fetch(API_GATEWAY_URL + '/generate-upload-url', {
        method: 'POST',
        headers: {
          "Content-Type": "application/json",
          "Authorization": auth_token,
        },
        body: JSON.stringify({
          user_id: userId,
          file_name: file.name,
          file_hash: fileHash,
        }),
      });

      if (!response.ok) {
        return setErrorStatus(setStatus, new Error(`Failed to get upload URL: ${response.statusText}`))
      }

      console.log(response);

      const { upload_url, submission_id } = await response.json();
      const contentType = file.type || 'application/octet-stream';

      setStatus('📤 Uploading to S3...');
      const uploadResult = await fetch(upload_url, {
        method: 'PUT',
        headers: {
          'Content-Type': contentType,
        },
        body: file,
      });

      if (!uploadResult.ok) {
        return setErrorStatus(setStatus, new Error(`Upload to S3 failed: ${uploadResult.statusText}`));
      }

      setStatus(`✅ Upload successful! Submission ID: ${submission_id}`);
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
      <button type="submit" disabled={!file}>Submit</button>
      {status && <p>{status}</p>}
    </form>
  );
}

export default SubmissionForm;
