// src/App.js
import React, { useState, useEffect } from 'react';
import { Authenticator } from '@aws-amplify/ui-react';
import { Amplify } from 'aws-amplify';
import { getCurrentUser, signOut } from 'aws-amplify/auth';
import '@aws-amplify/ui-react/styles.css';
import './App.css';

// These values come from terraform outputs
const COGNITO_USER_POOL_ID = process.env.REACT_APP_COGNITO_USER_POOL_ID;
const COGNITO_USER_POOL_CLIENT_ID = process.env.REACT_APP_COGNITO_USER_POOL_CLIENT_ID;
const API_GATEWAY_URL = process.env.REACT_APP_API_GATEWAY_URL;
const AWS_REGION = process.env.REACT_APP_AWS_REGION;

// Initialize Amplify with Cognito configuration
Amplify.configure({
  // Auth configuration for Amplify v6+
  Auth: {
    Cognito: {
      userPoolId: COGNITO_USER_POOL_ID,
      userPoolClientId: COGNITO_USER_POOL_CLIENT_ID,
      region: AWS_REGION
    }
  },
  // API configuration
  API: {
    REST: {
      HistoryLearningAPI: {
        endpoint: API_GATEWAY_URL,
        region: AWS_REGION
      }
    }
  }
});

function App() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuthState();
  }, []);

  async function checkAuthState() {
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

  async function handleSignOut() {
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

  return (
    <div className="app-container">
      {user ? (
        <div className="greeting-container">
          <h1>History Learning Platform</h1>
          <p>Welcome, {user.username}!</p>
          <p>You are now logged in to the History Learning Platform.</p>
          <div className="dashboard-container">
            <h2>Your Dashboard</h2>
            <p>This is where you would see your learning progress and activities.</p>
            {/* Add dashboard components here in the future */}
          </div>
          <button onClick={handleSignOut} className="sign-out-button">Sign Out</button>
        </div>
      ) : (
        <div className="login-container">
          <h1>History Learning Platform</h1>
          <p>Please sign in to access your learning materials</p>
          <Authenticator
            initialState="signIn"
            components={{
              // Hide "Create Account" option since admin creates accounts
              SignUp: () => null,
            }}
            services={{
              accountRecovery: {
                // Disable account recovery flow
                enabled: false
              }
            }}
          >
            {({ signOut }) => (
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
