import React, { useState } from 'react';
import { fetchAuthSession } from '@aws-amplify/auth';

interface Props {
  userId: string;
}

type SetStatus = React.Dispatch<React.SetStateAction<string | null>>;

// Use optional chaining instead of non-null assertion
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
const IS_DEV = import.meta.env.DEV;

async function getSessionToken(): Promise<string|undefined> {
  if (IS_DEV) {
    return 'dev-token';
  }
  try {
    const session = await fetchAuthSession();
    // Get the JWT token string - Amplify v6 format
    return session.tokens?.idToken?.toString();
  } catch (error) {
    console.error("Error getting auth session:", error);
    return undefined;
  }
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
        return setErrorStatus(setStatus, new Error('Not logged in or unable to retrieve authentication token'));
      }

      // Check if API Gateway URL is defined
      if (!BACKEND_URL) {
        return setErrorStatus(setStatus, new Error('Backend URL is not defined'));
      }

      setStatus('🔗 Requesting upload URL...');
      // Add 'Bearer ' prefix to the token
      const response = await fetch(BACKEND_URL + '/generate-upload-url', {
        method: 'POST',
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${auth_token}`,
        },
        body: JSON.stringify({
          user_id: userId,
          file_name: file.name,
          file_hash: fileHash,
        }),
      });

      // Log the full response for debugging
      console.log("API Response status:", response.status);
      console.log("API Response headers:", response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("API Error Response:", errorText);
        return setErrorStatus(
          setStatus,
          new Error(`Failed to get upload URL: ${response.status} ${response.statusText}`)
        );
      }

      const data = await response.json();
      console.log("API Response data:", data);

      const { upload_url, submission_id } = data;
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
        accept=".txt,.pdf,.jpg,.jpeg,.png,.docx,.doc,.rtf,.html,.htm,.md"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button type="submit" disabled={!file}>Submit</button>
      {status && <p>{status}</p>}
    </form>
  );
}

export default SubmissionForm;
