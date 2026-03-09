export interface AuthUser {
  id: number;
  username: string;
  pen_name?: string | null;
  email?: string | null;
}

const AUTH_STORAGE_KEY = 'spb_auth_user';
const TOKEN_STORAGE_KEY = 'spb_access_token';

export function getAuthUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setAuthUser(user: AuthUser | null, accessToken?: string | null) {
  if (!user) {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    return;
  }
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
  if (accessToken != null) {
    localStorage.setItem(TOKEN_STORAGE_KEY, accessToken);
  }
}

export function isLoggedIn() {
  return !!getAuthUser() && !!getAccessToken();
}
