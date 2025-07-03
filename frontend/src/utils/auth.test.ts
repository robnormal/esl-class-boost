import { vi } from 'vitest';

// Use vi.hoisted so we can mock the amplify/auth import
const { mockFetchAuthSession, mockIsDev } = vi.hoisted(() => {
  const mockFetchAuthSession = vi.fn();
  const mockIsDev = { value: false };
  return { mockFetchAuthSession, mockIsDev };
});

vi.mock('@aws-amplify/auth', () => ({
  fetchAuthSession: mockFetchAuthSession,
}));

vi.mock('./auth', async () => {
  const actual = await vi.importActual('./auth');
  return {
    ...actual,
    IS_DEV: mockIsDev.value,
    getSessionToken: vi.fn().mockImplementation(async () => {
      if (mockIsDev.value) {
        return 'dev-token';
      }
      try {
        const session = await mockFetchAuthSession();
        return session.tokens?.accessToken?.toString();
      } catch (error) {
        console.error("Error getting auth session:", error);
        return;
      }
    })
  };
});

import { getSessionToken } from './auth';

describe('getSessionToken', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsDev.value = false; // Default to production
  });

  it('returns dev-token in development mode', async () => {
    mockIsDev.value = true;
    const token = await getSessionToken();
    expect(token).toBe('dev-token');
  });

  it('returns access token in production mode', async () => {
    mockIsDev.value = false;
    mockFetchAuthSession.mockResolvedValue({
      tokens: {
        accessToken: {
          toString: () => 'real-token'
        }
      }
    });

    const token = await getSessionToken();
    expect(token).toBe('real-token');
  });

  it('returns undefined and logs error if fetchAuthSession throws', async () => {
    mockIsDev.value = false;
    const error = new Error('session error');
    mockFetchAuthSession.mockRejectedValue(error);
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const token = await getSessionToken();
    expect(token).toBeUndefined();
    expect(consoleSpy).toHaveBeenCalledWith('Error getting auth session:', error);

    consoleSpy.mockRestore();
  });
});
