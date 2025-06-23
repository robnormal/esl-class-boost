import React from 'react';
import { Link } from 'react-router-dom';
import SubmissionForm from './SubmissionForm';

interface DashboardProps {
  user: {
    username: string;
    userId?: string;
  };
}

function Dashboard({ user }: DashboardProps) {
  return (
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
    </div>
  );
}

export default Dashboard; 