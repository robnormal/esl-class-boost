import React, { useState, useEffect, JSX } from 'react';
import { Authenticator } from '@aws-amplify/ui-react';
import { Amplify } from 'aws-amplify';
import { getCurrentUser, signOut } from 'aws-amplify/auth';
import '@aws-amplify/ui-react/styles.css';
import './App.css';
import SubmissionForm from './SubmissionForm';
import { Routes, Route, useNavigate, Link } from 'react-router-dom';
import SubmissionDetails from './SubmissionDetails';
import SubmissionsList from './SubmissionsList';

type CurrentUser = Awaited<ReturnType<typeof getCurrentUser>>;

const IS_DEV = import.meta.env.DEV;
const COGNITO_USER_POOL_ID = import.meta.env.VITE_COGNITO_USER_POOL_ID;
const COGNITO_USER_POOL_CLIENT_ID = import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID;
const COGNITO_DOMAIN = import.meta.env.VITE_COGNITO_DOMAIN;
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

// Configure Amplify only in production
if (!IS_DEV) {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: COGNITO_USER_POOL_ID,
        userPoolClientId: COGNITO_USER_POOL_CLIENT_ID,
        loginWith: {
          oauth: {
            domain: COGNITO_DOMAIN,
            scopes: ["openid", "email", "profile"],
            redirectSignIn: [`${BACKEND_URL}/auth/callback`],
            redirectSignOut: [`${BACKEND_URL}/logout`],
            responseType: "token"
          }
        }
      }
    }
  });
}

import { useParams } from 'react-router-dom';

function SubmissionDetailsWrapper() {
  const { submissionId } = useParams();
  if (!submissionId) return <div>Invalid submission ID</div>;
  return <SubmissionDetails submissionId={submissionId} />;
}

function App(): JSX.Element {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const navigate = useNavigate();

  useEffect(() => {
    checkAuthState();
  }, []);

  async function checkAuthState(): Promise<void> {
    if (IS_DEV) {
      // Mock user for development
      setUser({username: 'dev-user', userId: 'dev-user-id'});
      setIsLoading(false);
      return;
    }

    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.log('Not authenticated');
      console.log(error);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSignOut(): Promise<void> {
    try {
      await signOut();
      setUser(null);
    } catch (error) {
      console.log('Error signing out: ', error);
    }
  }

  if (isLoading) {
    return <div className="app-container">Loading...</div>;
  }

  const components = {
    SignIn: {
      Footer() {
        return null;
      },
    },
  };

  return (
    <div className="app-container">
      <Routes>
        <Route path="/" element={
          user ? (
            <div className="greeting-container">
              <h1>History Learning Platform</h1>
              <p>Welcome, {user.username}!</p>
              <div className="dashboard-container">
                <h2>Your Dashboard</h2>
                <div className="submission-form">
                  <SubmissionForm userId={user.username}/>
                </div>
                <div className="dashboard-actions">
                  <Link to="/submissions" className="button">View My Submissions</Link>
                </div>
              </div>
              <button onClick={handleSignOut} className="sign-out-button">
                Sign Out
              </button>
            </div>
          ) : (
            <div className="login-container">
              <h1>History Learning Platform</h1>
              <p>Please sign in to access your learning materials</p>
              <Authenticator initialState="signIn" hideSignUp components={components}>
                {({signOut}: { signOut?: () => void }) => (
                  <div>
                    <h2>Welcome back!</h2>
                    <p>You've successfully signed in.</p>
                    <button onClick={signOut}>Sign out</button>
                  </div>
                )}
              </Authenticator>
            </div>
          )
        }/>
        <Route path="/submission/:submissionId" element={<SubmissionDetailsWrapper/>}/>
        <Route path="/submissions" element={
          user ? <SubmissionsList userId={user.username} /> : <div>Please sign in to view your submissions</div>
        }/>
      </Routes>
    </div>
  );
}

export default App;
