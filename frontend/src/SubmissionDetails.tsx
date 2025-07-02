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

interface WordDefinition {
  word: string;
  results?: { definition: string; partOfSpeech?: string }[];
  error?: string;
}

const SubmissionDetails: React.FC<SubmissionDetailsProps> = ({ submissionId }) => {
  const [details, setDetails] = useState<ParagraphDetails[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  // Track which paragraphs are expanded
  const [expanded, setExpanded] = useState<{ [index: number]: boolean }>({});
  // Cache paragraphs once fetched
  const [allParagraphs, setAllParagraphs] = useState<string[] | null>(null);
  const [definitionModal, setDefinitionModal] = useState<{
    word: string;
    definitions: WordDefinition | null;
    open: boolean;
    loading: boolean;
    error: string | null;
  }>({ word: '', definitions: null, open: false, loading: false, error: null });

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

  const fetchWordDefinition = async (word: string) => {
    setDefinitionModal({ word, definitions: null, open: true, loading: true, error: null });
    try {
      const response = await fetch(`${BACKEND_URL}/definition/${encodeURIComponent(word)}`);
      if (!response.ok) {
        throw new Error('Failed to fetch definition');
      }
      const data = await response.json();
      setDefinitionModal({ word, definitions: { word, results: data }, open: true, loading: false, error: null });
    } catch (err) {
      setDefinitionModal({ word, definitions: null, open: true, loading: false, error: 'Failed to fetch definition' });
    }
  };

  const closeModal = () => {
    setDefinitionModal(prev => ({ ...prev, open: false }));
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
            <span className="expand-toggle">
              [{expanded[detail.paragraph_index] ? 'Collapse' : 'Expand'}]
            </span>
          </h3>
          <div className="paragraph-summary">{detail.summary}</div>
          <div className="vocabulary-section">
            <div className="vocabulary-title">Vocabulary Words</div>
            <ul className="vocabulary-list">
              {detail.vocabulary.map((word, i) => (
                <li key={i}>
                  <button
                    className="vocab-word-btn"
                    onClick={() => fetchWordDefinition(word)}
                    title={`Show definition for ${word}`}
                  >
                    {word}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ))}
      {/* Definition Modal */}
      {definitionModal.open && (
        <div
          className="modal-overlay"
          onClick={closeModal}
        >
          <div
            className="modal-content"
            onClick={e => e.stopPropagation()}
          >
            <button
              onClick={closeModal}
              className="modal-close-btn"
              aria-label="Close"
            >
              ×
            </button>
            <h2>Definition: {definitionModal.word}</h2>
            {definitionModal.loading && <div>Loading...</div>}
            {definitionModal.error && <div className="definition-error">{definitionModal.error}</div>}
            {definitionModal.definitions && definitionModal.definitions.results && definitionModal.definitions.results.length > 0 ? (
              <ul>
                {definitionModal.definitions.results.map((def, idx) => (
                  <li key={idx}>
                    <strong>{def.partOfSpeech ? `${def.partOfSpeech}: ` : ''}</strong>
                    {def.definition}
                  </li>
                ))}
              </ul>
            ) : (
              !definitionModal.loading && !definitionModal.error && <div>No definition found.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SubmissionDetails;
