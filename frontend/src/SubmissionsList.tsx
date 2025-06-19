import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSessionToken, BACKEND_URL } from './utils/auth';

interface Submission {
  id: string;
  filename: string;
  created_at: number;
  status: string;
}

interface SubmissionsListProps {
  userId: string;
}

type SetError = React.Dispatch<React.SetStateAction<string | null>>

function setAndShowError(err: unknown, setError: SetError) {
  if (err instanceof Error) {
    setError(err.message);
  } else {
    setError(`Unknown error: ${err}`);
  }
  console.error(err);
}

const SubmissionsList: React.FC<SubmissionsListProps> = ({ userId }) => {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSubmissions = async () => {
      try {
        setLoading(true);

        const authToken = await getSessionToken();
        if (!authToken) {
          setAndShowError('Not logged in or unable to retrieve authentication token', setError);
        } else if (!BACKEND_URL) {
          setAndShowError('Backend URL is not defined', setError);
        } else {
          const response = await fetch(`${BACKEND_URL}/submissions`, {
            headers: {
              "Authorization": `Bearer ${authToken}`,
            },
          });

          if (!response.ok) {
            setAndShowError(`Failed to fetch submissions: ${response.status} ${response.statusText}`, setError);
          } else {
            const data = await response.json();
            setSubmissions(data.submissions);
          }
        }
      } catch (err) {
        setAndShowError(err, setError)
      } finally {
        setLoading(false);
      }
    };

    fetchSubmissions();
  }, [userId]);

  if (loading) {
    return <div className="submissions-container">Loading your submissions...</div>;
  }

  if (error) {
    return <div className="submissions-container error">Error: {error}</div>;
  }

  if (submissions.length === 0) {
    return (
      <div className="submissions-container empty">
        <h2>Your Submissions</h2>
        <p>You haven't uploaded any documents yet.</p>
        <Link to="/" className="button">Upload a Document</Link>
      </div>
    );
  }

  return (
    <div className="submissions-container">
      <h2>Your Submissions</h2>
      <div className="submissions-list">
        <div className="submissions-header">
          <span className="filename-column">Filename</span>
          <span className="date-column">Date</span>
          <span className="status-column">Status</span>
          <span className="actions-column">Actions</span>
        </div>
        {submissions.map((submission) => (
          <div key={submission.id} className="submission-item">
            <span className="filename-column">{submission.filename}</span>
            <span className="date-column">{new Date(submission.created_at * 1000).toLocaleDateString()}</span>
            <span className="status-column">{submission.status}</span>
            {submission.status === 'paragraphed' && (
              <span className="actions-column">
                <Link to={`/submission/${submission.id}`} className="view-button">
                  View Details
                </Link>
              </span>
            )}
          </div>
        ))}
      </div>
      <Link to="/" className="button add-submission">Upload Another Document</Link>
    </div>
  );
};

export default SubmissionsList;
