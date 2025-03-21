// src/App.js
import React, { useState, useEffect } from 'react';
import { Authenticator } from '@aws-amplify/ui-react';
import { Amplify } from 'aws-amplify';
import Auth from 'aws-amplify/auth';
import '@aws-amplify/ui-react/styles.css';
import './App.css';

const COGNITO_DOMAIN = process.env.COGNITO_DOMAIN; // 'rhr79-history-learning-prod.auth.us-east-2.amazoncognito.com';
const COGNITO_USER_POOL_ID = process.env.COGNITO_USER_POOL_ID;
const COGNITO_USER_POOL_CLIENT_ID = process.env.COGNITO_USER_POOL_CLIENT_ID;
const CLOUDFRONT_DOMAIN = process.env.CLOUDFRONT_DOMAIN;
const API_GATEWAY_URL = process.env.API_GATEWAY_URL;
const AWS_REGION = process.env.AWS_REGION;

// Initialize Amplify with Cognito configuration
// These values would come from your CloudFront outputs
Amplify.configure({
  // Auth configuration for Amplify v6+
  Auth: {
    Cognito: {
      userPoolId: COGNITO_USER_POOL_ID, // Replace with aws_cognito_user_pool.user_pool.id from terraform output
      userPoolClientId: COGNITO_USER_POOL_CLIENT_ID, // Replace with aws_cognito_user_pool_client.user_pool_client.id from terraform output
      loginWith: {
        oauth: {
          domain: COGNITO_DOMAIN, // From terraform output: cognito_domain (without the https://)
          scopes: ['email', 'openid', 'profile'],
          responseType: 'code',
          redirectSignIn: ['https://' + CLOUDFRONT_DOMAIN + '/auth/callback'], // Replace with aws_cloudfront_distribution.website.domain_name
          redirectSignOut: ['https://' + CLOUDFRONT_DOMAIN + '/logout'], // Replace with aws_cloudfront_distribution.website.domain_name
        }
      }
    }
  },
  // API configuration
  API: {
    REST: {
      HistoryLearningAPI: {
        endpoint: API_GATEWAY_URL, // Replace with aws_api_gateway_deployment.api_deployment.invoke_url
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
      const userData = await Auth.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.log('Not authenticated');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSignOut() {
    try {
      await Auth.signOut();
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
          <Authenticator loginMechanisms={['email']} socialProviders={[]}>
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
