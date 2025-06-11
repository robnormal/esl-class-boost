import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fetchAuthSession } from '@aws-amplify/auth';

interface Submission {
  id: string;
  filename: string;
  created_at: number;
  status: string;
}

interface SubmissionsListProps {
  userId: string;
}

// Use environment variables for configuration
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
const IS_DEV = import.meta.env.DEV;

async function getSessionToken(): Promise<string|undefined> {
  if (IS_DEV) {
    return 'dev-token';
  }
  try {
    const session = await fetchAuthSession();
    return session.tokens?.idToken?.toString();
  } catch (error) {
    console.error("Error getting auth session:", error);
    return undefined;
  }
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
          throw new Error('Not logged in or unable to retrieve authentication token');
        }

        if (!BACKEND_URL) {
          throw new Error('Backend URL is not defined');
        }

        const response = await fetch(`${BACKEND_URL}/submissions`, {
          headers: {
            "Authorization": `Bearer ${authToken}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch submissions: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        setSubmissions(data.submissions);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError(`Unknown error: ${err}`);
        }
        console.error(err);
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
