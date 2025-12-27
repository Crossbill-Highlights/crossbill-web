// Module-level token storage (not accessible to XSS)
// This is kept separate from AuthContext to avoid circular dependency with axios-instance

let accessToken: string | null = null;
let tokenExpiresAt: number | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null, expiresIn?: number): void {
  accessToken = token;
  if (token && expiresIn) {
    tokenExpiresAt = Date.now() + expiresIn * 1000;
  } else {
    tokenExpiresAt = null;
  }
}

export function getTokenExpiresAt(): number | null {
  return tokenExpiresAt;
}

export function clearTokens(): void {
  accessToken = null;
  tokenExpiresAt = null;
}
