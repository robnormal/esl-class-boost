import React, { useState, useEffect, JSX } from 'react';
import { Authenticator } from '@aws-amplify/ui-react';
import { Amplify } from 'aws-amplify';
import { getCurrentUser, signOut } from 'aws-amplify/auth';
import './App.css';
import { Routes, Route, Link } from 'react-router-dom';
import SubmissionDetails from './SubmissionDetails';
import SubmissionsList from './SubmissionsList';
import Dashboard from './Dashboard';
import { useParams } from 'react-router-dom';

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

function SubmissionDetailsWrapper() {
  const { submissionId } = useParams();
  if (!submissionId) return <div>Invalid submission ID</div>;
  return <SubmissionDetails submissionId={submissionId} />;
}

function AuthenticatedApp({ user }: { user: CurrentUser }) {
  async function handleSignOut(): Promise<void> {
    try {
      await signOut();
    } catch (error) {
      console.log('Error signing out: ', error);
    }
  }

  return (
    <div className="app-container">
      <nav className="app-nav">
        <Link to="/" className="nav-link">Home</Link>
        <Link to="/submissions" className="nav-link">My Submissions</Link>
        <button onClick={handleSignOut} className="sign-out-button">
          Sign Out
        </button>
      </nav>

      <Routes>
        <Route path="/" element={<Dashboard user={user} />}/>
        <Route path="/submission/:submissionId" element={<SubmissionDetailsWrapper/>}/>
        <Route path="/submissions" element={<SubmissionsList userId={user.username} />}/>
      </Routes>
    </div>
  );
}

function App(): JSX.Element {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

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

  // In development, show authenticated app directly
  if (IS_DEV && user) {
    return <AuthenticatedApp user={user} />;
  }

  // In production, wrap everything with Authenticator
  if (!IS_DEV) {
    return (
      <Authenticator initialState="signIn" hideSignUp components={components}>
        {({ user: amplifyUser }) => {
          // Update local user state when Amplify user changes
          if (amplifyUser && !user) {
            setUser(amplifyUser);
          }

          return user ? <AuthenticatedApp user={user} /> : <div>Loading...</div>;
        }}
      </Authenticator>
    );
  }

  // Development without authenticated user - show login prompt
  return (
    <div className="app-container">
      <div className="login-container">
        <h1>History Learning Platform</h1>
        <p>Development mode - please authenticate to continue</p>
        <button onClick={checkAuthState}>Check Authentication</button>
      </div>
    </div>
  );
}

export default App;
