import React, { useState, useEffect, JSX } from 'react';
import { Amplify } from 'aws-amplify';
import { getCurrentUser, signOut, signIn } from 'aws-amplify/auth';
import './App.css';
import { Routes, Route, Link } from 'react-router-dom';
import SubmissionDetails from './SubmissionDetails';
import SubmissionsList from './SubmissionsList';
import Dashboard from './Dashboard';
import { useParams } from 'react-router-dom';
import SignInForm from './SignInForm';

type CurrentUser = Awaited<ReturnType<typeof getCurrentUser>>;

const IS_DEV = import.meta.env.DEV;
const COGNITO_USER_POOL_ID = import.meta.env.VITE_COGNITO_USER_POOL_ID;
const COGNITO_USER_POOL_CLIENT_ID = import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID;
const COGNITO_DOMAIN = import.meta.env.VITE_COGNITO_DOMAIN;

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
            redirectSignIn: [window.location.origin + "/auth/callback"],
            redirectSignOut: [window.location.origin + "/logout"],
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

function AuthenticatedApp({ user, onSignOut }: { user: CurrentUser; onSignOut: () => Promise<void> }) {
  async function handleSignOut(): Promise<void> {
    try {
      await signOut();
      await onSignOut(); // Call the parent's callback to update state
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
        <Route path="/auth/callback" element={<div>Authenticating...</div>}/>
        <Route path="/logout" element={<div>Logging out...</div>}/>
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

  async function onSignOut(): Promise<void> {
    setUser(null);
  }

  async function handleCustomSignIn(username: string, password: string): Promise<void> {
    const result = await signIn({ username, password });

    if (result.isSignedIn) {
      // User is signed in, refresh our state
      await checkAuthState();
    } else if (result.nextStep) {
      // We don't want to go through additional steps like verification so we'll set the current user anyway
      try {
        const userData = await getCurrentUser();
        setUser(userData);
      } catch (error) {
        throw new Error('Authentication incomplete. Please contact your administrator.');
      }
    }
  }

  if (isLoading) {
    return <div className="app-container">Loading...</div>;
  } else if (user) {
    // If user is authenticated, show the app
    return <AuthenticatedApp user={user} onSignOut={onSignOut} />;
  } else if (!IS_DEV) {
    // Show sign-in form in production
    return <SignInForm onSignIn={handleCustomSignIn} />;
  } else {
    // Show login prompt in development
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
}

export default App;
