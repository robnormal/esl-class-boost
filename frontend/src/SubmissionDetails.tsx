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
  // Track expanded paragraphs
  const [expanded, setExpanded] = useState<{ [index: number]: boolean }>({});
  // Store all paragraphs once fetched
  const [allParagraphs, setAllParagraphs] = useState<string[] | null>(null);

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

      const data = await response.json();
      if (!Array.isArray(data.paragraphs)) {
        throw new Error('Invalid response format: paragraphs not found');
      }
      const text = data.paragraphs.join('\n\n');
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

  // Fetch all paragraphs if not already fetched
  const fetchAllParagraphs = async () => {
    if (allParagraphs !== null) return allParagraphs;
    try {
      const authToken = await getSessionToken();
      if (!authToken) {
        alert('Not logged in or unable to retrieve authentication token');
        return null;
      }
      const response = await fetch(`${BACKEND_URL}/files/${submissionId}/text`, {
        headers: {
          "Authorization": `Bearer ${authToken}`,
        },
      });
      if (!response.ok) {
        throw new Error('Failed to fetch paragraphs');
      }
      const data = await response.json();
      if (!Array.isArray(data.paragraphs)) {
        throw new Error('Invalid response format: paragraphs not found');
      }
      setAllParagraphs(data.paragraphs);
      return data.paragraphs;
    } catch (err) {
      alert('Failed to fetch paragraphs');
      return null;
    }
  };

  const handleToggleParagraph = async (index: number) => {
    setExpanded(prev => ({ ...prev, [index]: !prev[index] }));
    if (!expanded[index]) {
      // Only fetch if expanding and not already fetched
      if (!allParagraphs) {
        const paragraphs = await fetchAllParagraphs();
        if (!paragraphs) return;
      }
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
          <h3
            className="paragraph-start"
            onClick={() => handleToggleParagraph(detail.paragraph_index)}
            title="Click to expand/collapse paragraph"
          >
            {expanded[detail.paragraph_index] && allParagraphs && allParagraphs[detail.paragraph_index]
              ? allParagraphs[detail.paragraph_index]
              : detail.paragraph_start + '...'}
            <span style={{ marginLeft: 8, fontSize: '0.8em', color: '#0074d9' }}>
              [{expanded[detail.paragraph_index] ? 'Collapse' : 'Expand'}]
            </span>
          </h3>
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
