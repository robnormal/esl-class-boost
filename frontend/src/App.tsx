// src/App.tsx
import React, { useState, useEffect, JSX } from 'react';
import { Authenticator } from '@aws-amplify/ui-react';
import { Amplify } from 'aws-amplify';
import { getCurrentUser, signOut } from 'aws-amplify/auth';
import '@aws-amplify/ui-react/styles.css';
import './App.css';

type CurrentUser = Awaited<ReturnType<typeof getCurrentUser>>;

// Environment variables
const COGNITO_USER_POOL_ID = process.env.REACT_APP_COGNITO_USER_POOL_ID!;
const COGNITO_USER_POOL_CLIENT_ID = process.env.REACT_APP_COGNITO_USER_POOL_CLIENT_ID!;
const API_GATEWAY_URL = process.env.REACT_APP_API_GATEWAY_URL!;
const AWS_REGION = process.env.REACT_APP_AWS_REGION!;

// Configure Amplify
Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: COGNITO_USER_POOL_ID,
      userPoolClientId: COGNITO_USER_POOL_CLIENT_ID,
    },
  },
  API: {
    REST: {
      HistoryLearningAPI: {
        endpoint: API_GATEWAY_URL,
        region: AWS_REGION,
      },
    },
  },
});

function App(): JSX.Element {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    checkAuthState();
  }, []);

  async function checkAuthState(): Promise<void> {
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
      {user ? (
        <div className="greeting-container">
          <h1>History Learning Platform</h1>
          <p>Welcome, {user.username}!</p>
          <div className="dashboard-container">
            <h2>Your Dashboard</h2>
            <p>This is where you would see your learning progress and activities.</p>

            {/* ✅ Submission Form */}
            <div className="submission-form">
              <h3>Submit a File</h3>
              <form onSubmit={(e) => {
                e.preventDefault();
                const fileInput = document.getElementById('fileInput') as HTMLInputElement;
                if (fileInput?.files?.[0]) {
                  const file = fileInput.files[0];
                  // TODO: Handle file upload logic
                  console.log('Selected file:', file);
                }
              }}>
                <input type="file" id="fileInput" accept=".txt,.pdf,.docx,.html,.md,.png,.jpg" />
                <button type="submit">Submit</button>
              </form>
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
            {({ signOut }: { signOut?: () => void }) => (
              <div>
                <h2>Welcome back!</h2>
                <p>You've successfully signed in.</p>
                <button onClick={signOut}>Sign out</button>
              </div>
            )}
          </Authenticator>
        </div>
      )}
    </div>
  );
}

export default App;
