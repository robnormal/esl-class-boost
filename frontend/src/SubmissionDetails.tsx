// frontend/src/SubmissionDetails.tsx
import React, { useState, useEffect } from 'react';
import { getSessionToken } from './utils/auth';

interface ParagraphDetails {
  paragraph_index: number;
  vocabulary: string[];
  summary: string;
  paragraph_start: string;
}

interface SubmissionDetailsProps {
  submissionId: string;
}

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

const SubmissionDetails: React.FC<SubmissionDetailsProps> = ({ submissionId }) => {
  const [details, setDetails] = useState<ParagraphDetails[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const downloadPlainText = async () => {
    try {
      const authToken = await getSessionToken();
      if (!authToken) {
        alert('Not logged in or unable to retrieve authentication token');
        return;
      }

      const response = await fetch(`${BACKEND_URL}/files/${submissionId}/text`, {
        headers: {
          "Authorization": `Bearer ${authToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to download plain text');
      }

      const text = await response.text();
      const url = URL.createObjectURL(new Blob([text], { type: 'text/plain' }));
      const fake_a = document.createElement('a');
      fake_a.href = url;
      fake_a.download = `submission-${submissionId}.txt`;
      document.body.appendChild(fake_a);
      fake_a.click(); // Downloading starts here
      document.body.removeChild(fake_a);
      URL.revokeObjectURL(url);

    } catch (err) {
      console.error('Error downloading plain text:', err);
      alert('Failed to download plain text');
    }
  };

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const authToken = await getSessionToken();
        if (!authToken) {
          setError('Not logged in or unable to retrieve authentication token');
          return;
        }

        const response = await fetch(`${BACKEND_URL}/files/${submissionId}/details`, {
          headers: {
            "Authorization": `Bearer ${authToken}`,
          },
        });
        if (!response.ok) {
          throw new Error('Failed to fetch submission details');
        }
        const data = await response.json();
        setDetails(data.details);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError(`Unknown error: ${err}`)
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [submissionId]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1 className="document-title">Study Guide</h1>
      <div className="download-section">
        <button onClick={downloadPlainText} className="download-link">
          Download Plain Text
        </button>
      </div>
      {details.map((detail, index) => (
        <div key={index} className="paragraph-study-guide">
          <h3 className="paragraph-start">{detail.paragraph_start}...</h3>
          <div className="paragraph-summary">{detail.summary}</div>
          <div className="vocabulary-section">
            <div className="vocabulary-title">Vocabulary Words</div>
            <ul className="vocabulary-list">
              {detail.vocabulary.map((word, i) => (
                <li key={i}>{word}</li>
              ))}
            </ul>
          </div>
        </div>
      ))}
    </div>
  );
};

export default SubmissionDetails;
