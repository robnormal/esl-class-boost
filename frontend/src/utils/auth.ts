import { fetchAuthSession } from '@aws-amplify/auth';

export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
export const IS_DEV = import.meta.env.DEV;

export async function getSessionToken(): Promise<string|undefined> {
  if (IS_DEV) {
    return 'dev-token';
  }
  try {
    const session = await fetchAuthSession();
    return session.tokens?.accessToken?.toString();
  } catch (error) {
    console.error("Error getting auth session:", error);
    return;
  }
}
