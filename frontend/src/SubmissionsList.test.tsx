import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SubmissionsList from './SubmissionsList';
import { vi } from 'vitest';

// Use vi.hoisted to properly handle mocked variables
const { mockGetSessionToken, mockBackendUrl } = vi.hoisted(() => {
  const mockGetSessionToken = vi.fn();
  const mockBackendUrl = { value: 'http://mock-api.com' };
  return { mockGetSessionToken, mockBackendUrl };
});

// Mock the auth utility
vi.mock('./utils/auth', () => ({
  getSessionToken: mockGetSessionToken,
  get BACKEND_URL() { return mockBackendUrl.value; }
}));

// Mock fetch globally
const mockFetch = vi.fn();
(global as any).fetch = mockFetch;

describe('SubmissionsList', () => {
  const mockUserId = 'test-user';

  beforeEach(() => {
    vi.clearAllMocks();
    mockBackendUrl.value = 'http://mock-api.com'; // Reset to default
    mockFetch.mockClear();
  });

  it('displays loading state while fetching submissions', async () => {
    mockGetSessionToken.mockResolvedValue('mock-token');
    // Mock fetch to return a pending promise to keep loading state
    let resolveFetch: (value: any) => void;
    const fetchPromise = new Promise(resolve => {
      resolveFetch = resolve;
    });
    mockFetch.mockReturnValue(fetchPromise);
    
    render(
      <MemoryRouter>
        <SubmissionsList userId={mockUserId} />
      </MemoryRouter>
    );
    
    // Check loading state before fetch resolves
    expect(screen.getByText(/Loading your submissions.../i)).toBeInTheDocument();
    
    // Clean up by resolving the fetch inside act
    await act(async () => {
      resolveFetch!({
        ok: true,
        json: () => Promise.resolve({ submissions: [] })
      });
      // Wait for the promise to resolve and state updates to complete
      await fetchPromise;
    });
  });

  it('displays error state when token retrieval fails', async () => {
    mockGetSessionToken.mockResolvedValue(undefined);
    await act(async () => {
      render(
        <MemoryRouter>
          <SubmissionsList userId={mockUserId} />
        </MemoryRouter>
      );
    });
    await waitFor(() => {
      expect(screen.getByText(/Error: Not logged in or unable to retrieve authentication token/i)).toBeInTheDocument();
    });
  });

  it('displays error state when backend URL is not defined', async () => {
    mockGetSessionToken.mockResolvedValue('mock-token');
    mockBackendUrl.value = ''; // Set backend URL to empty string
    
    await act(async () => {
      render(
        <MemoryRouter>
          <SubmissionsList userId={mockUserId} />
        </MemoryRouter>
      );
    });
    await waitFor(() => {
      expect(screen.getByText(/Error: Backend URL is not defined/i)).toBeInTheDocument();
    });
  });

  it('displays error state when API fetch fails', async () => {
    mockGetSessionToken.mockResolvedValue('mock-token');
    mockFetch.mockRejectedValue(new Error('API error'));
    
    await act(async () => {
      render(
        <MemoryRouter>
          <SubmissionsList userId={mockUserId} />
        </MemoryRouter>
      );
    });
    await waitFor(() => {
      expect(screen.getByText(/Error: API error/i)).toBeInTheDocument();
    });
  });

  it('displays empty state when there are no submissions', async () => {
    mockGetSessionToken.mockResolvedValue('mock-token');
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ submissions: [] })
    });
    
    await act(async () => {
      render(
        <MemoryRouter>
          <SubmissionsList userId={mockUserId} />
        </MemoryRouter>
      );
    });
    await waitFor(() => {
      expect(screen.getByText(/You haven't uploaded any documents yet./i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Upload a Document/i })).toHaveAttribute('href', '/');
    });
  });

  it('displays list of submissions when data is available', async () => {
    mockGetSessionToken.mockResolvedValue('mock-token');
    const mockSubmissions = [
      { id: '1', filename: 'test1.pdf', created_at: 1630000000, status: 'complete' },
      { id: '2', filename: 'test2.pdf', created_at: 1631000000, status: 'processing' }
    ];
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ submissions: mockSubmissions })
    });
    
    await act(async () => {
      render(
        <MemoryRouter>
          <SubmissionsList userId={mockUserId} />
        </MemoryRouter>
      );
    });
    await waitFor(() => {
      expect(screen.getByText('test1.pdf')).toBeInTheDocument();
      expect(screen.getByText('test2.pdf')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /View Details/i })).toHaveAttribute('href', '/submission/1');
      expect(screen.getAllByText(/complete|processing/).length).toBe(2);
      expect(screen.getByRole('link', { name: /Upload Another Document/i })).toHaveAttribute('href', '/');
    });
  });
});
