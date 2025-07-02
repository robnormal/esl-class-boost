import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Dashboard from './Dashboard';

const mockUser = { username: 'testuser', userId: 'user-123' };

jest.mock('./SubmissionForm', () => (props: any) => (
  <div data-testid="submission-form-mock">SubmissionForm for {props.userId}</div>
));

describe('Dashboard', () => {
  it('renders greeting with username', () => {
    render(<Dashboard user={mockUser} />, { wrapper: MemoryRouter });
    expect(screen.getByText(/Welcome, testuser!/)).toBeInTheDocument();
  });

  it('renders SubmissionForm with correct userId', () => {
    render(<Dashboard user={mockUser} />, { wrapper: MemoryRouter });
    expect(screen.getByTestId('submission-form-mock')).toHaveTextContent('SubmissionForm for testuser');
  });

  it('renders link to submissions', () => {
    render(<Dashboard user={mockUser} />, { wrapper: MemoryRouter });
    const link = screen.getByRole('link', { name: /View My Submissions/i });
    expect(link).toHaveAttribute('href', '/submissions');
  });
}); 