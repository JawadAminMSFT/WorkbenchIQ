import { createHmac } from 'crypto';

const SESSION_MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours

/**
 * Scan process.env for AUTH_USER_* keys and parse "username:password" pairs.
 * Splits on the first colon only, so passwords may contain colons.
 */
export function getUsers(): Map<string, string> {
  const users = new Map<string, string>();
  for (const [key, value] of Object.entries(process.env)) {
    if (key.startsWith('AUTH_USER_') && value) {
      const colonIndex = value.indexOf(':');
      if (colonIndex > 0) {
        const username = value.substring(0, colonIndex);
        const password = value.substring(colonIndex + 1);
        users.set(username, password);
      }
    }
  }
  return users;
}

/**
 * Check if authentication is enabled (i.e., at least one AUTH_USER_* env var is set).
 */
export function isAuthEnabled(): boolean {
  return getUsers().size > 0;
}

function getSecret(): string {
  return process.env.AUTH_SECRET || 'workbenchiq-default-secret-change-me';
}

/**
 * Create an HMAC-signed session token embedding the username and timestamp.
 * Format: <hmac>.<username>.<timestamp>
 */
export function createSessionToken(username: string): string {
  const timestamp = Date.now().toString();
  const payload = `${username}.${timestamp}`;
  const hmac = createHmac('sha256', getSecret()).update(payload).digest('hex');
  return `${hmac}.${payload}`;
}

/**
 * Validate an HMAC-signed session token.
 * Returns the username if valid, or null if invalid/expired.
 */
export function validateSessionToken(token: string): string | null {
  if (!token) return null;

  const parts = token.split('.');
  if (parts.length < 3) return null;

  const receivedHmac = parts[0];
  const username = parts.slice(1, -1).join('.'); // username may contain dots
  const timestamp = parts[parts.length - 1];

  // Verify timestamp is a number
  const ts = parseInt(timestamp, 10);
  if (isNaN(ts)) return null;

  // Check expiration
  if (Date.now() - ts > SESSION_MAX_AGE_MS) return null;

  // Recompute HMAC and compare
  const payload = `${username}.${timestamp}`;
  const expectedHmac = createHmac('sha256', getSecret()).update(payload).digest('hex');

  // Constant-time comparison
  if (receivedHmac.length !== expectedHmac.length) return null;
  let mismatch = 0;
  for (let i = 0; i < receivedHmac.length; i++) {
    mismatch |= receivedHmac.charCodeAt(i) ^ expectedHmac.charCodeAt(i);
  }
  if (mismatch !== 0) return null;

  return username;
}
