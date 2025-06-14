// frontend/src/SubmissionDetails.tsx
import React, { useState, useEffect } from 'react';

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

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/files/${submissionId}/details`);
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
        <a href={`${BACKEND_URL}/files/${submissionId}/text`} className="download-link">
          Download Plain Text
        </a>
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
