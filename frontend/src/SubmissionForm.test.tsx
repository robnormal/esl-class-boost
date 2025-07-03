import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import SubmissionForm from './SubmissionForm';
import { vi } from 'vitest';

// --- Setup mocked dependencies ---

// Use vi.hoisted so we can access the mocked references in the vi.mock factory
const { mockGetSessionToken, mockBackendUrl, mockFetch } = vi.hoisted(() => {
  const mockGetSessionToken = vi.fn();
  const mockBackendUrl = { value: 'http://mock-api.com' };
  const mockFetch = vi.fn();
  return { mockGetSessionToken, mockBackendUrl, mockFetch };
});

// Mock the auth utility (getSessionToken + BACKEND_URL)
vi.mock('./utils/auth', () => ({
  getSessionToken: mockGetSessionToken,
  get BACKEND_URL() { return mockBackendUrl.value; }
}));

// Assign the mocked fetch to the global scope
(global as any).fetch = mockFetch;

// Mock browser crypto implementation used by hashFile
if (!(global as any).crypto) {
  (global as any).crypto = {
    "subtle": {
      digest: vi.fn().mockResolvedValue(new ArrayBuffer(32))
    } as any
  } as Crypto;
}

// Helper to create a mock File instance with an arrayBuffer implementation
function createMockFile(name = 'test.txt', type = 'text/plain', content = 'hello world') {
  const file = new File([content], name, { type });
  // Ensure arrayBuffer returns a simple ArrayBuffer to satisfy hashFile
  Object.defineProperty(file, 'arrayBuffer', {
    value: vi.fn().mockResolvedValue(new TextEncoder().encode(content).buffer),
    writable: true
  });
  return file;
}

const renderComponent = () => render(<SubmissionForm userId="user-123" />);

// --- Tests ---

describe('SubmissionForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockBackendUrl.value = 'http://mock-api.com';
  });

  it('shows error when submitting without selecting a file', async () => {
    renderComponent();

    const form = document.querySelector('form') as HTMLFormElement;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText(/please select a file to upload/i)).toBeInTheDocument();
    });
  });

  it('shows error when token retrieval fails', async () => {
    mockGetSessionToken.mockResolvedValue(undefined);

    renderComponent();
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = createMockFile();

    await act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
    });

    const form = document.querySelector('form') as HTMLFormElement;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText(/not logged in or unable to retrieve authentication token/i)).toBeInTheDocument();
    });
  });

  it('shows error when backend url is not defined', async () => {
    mockGetSessionToken.mockResolvedValue('mock-token');
    mockBackendUrl.value = '';

    renderComponent();
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = createMockFile();
    fireEvent.change(input, { target: { files: [file] } });

    const form = document.querySelector('form') as HTMLFormElement;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText(/backend url is not defined/i)).toBeInTheDocument();
    });
  });

  it('shows error when API returns non-ok response for upload url', async () => {
    mockGetSessionToken.mockResolvedValue('mock-token');
    // First fetch call - generate upload url returns 500
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      text: () => Promise.resolve('')
    });

    renderComponent();
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = createMockFile();
    fireEvent.change(input, { target: { files: [file] } });
    const form = document.querySelector('form') as HTMLFormElement;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText(/failed to get upload url/i)).toBeInTheDocument();
    });
  });

  it('displays success message after successful upload', async () => {
    mockGetSessionToken.mockResolvedValue('mock-token');

    // First fetch call - return upload_url & submission_id
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        upload_url: 'http://upload-url.com',
        submission_id: 'submission-123'
      }),
      headers: {},
      status: 200,
      statusText: 'OK'
    });

    // Second fetch call - uploading to S3 (PUT) succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      statusText: 'OK'
    });

    renderComponent();
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = createMockFile();
    fireEvent.change(input, { target: { files: [file] } });

    const form = document.querySelector('form') as HTMLFormElement;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText(/upload successful/i)).toBeInTheDocument();
      // The link to submissions should appear
      expect(screen.getByRole('link', { name: /view all submissions/i })).toHaveAttribute('href', '/submissions');
    });
  });
}); 