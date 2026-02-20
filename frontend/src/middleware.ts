import { NextRequest, NextResponse } from 'next/server';

const SESSION_MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours

/**
 * HMAC-SHA256 validation using Web Crypto API (Edge runtime compatible).
 */
async function validateSessionToken(token: string): Promise<string | null> {
  if (!token) return null;

  const secret = process.env.AUTH_SECRET || 'workbenchiq-default-secret-change-me';

  const parts = token.split('.');
  if (parts.length < 3) return null;

  const receivedHmac = parts[0];
  const username = parts.slice(1, -1).join('.');
  const timestamp = parts[parts.length - 1];

  const ts = parseInt(timestamp, 10);
  if (isNaN(ts)) return null;
  if (Date.now() - ts > SESSION_MAX_AGE_MS) return null;

  // Compute HMAC using Web Crypto API
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secret);
  const key = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const payload = `${username}.${timestamp}`;
  const signature = await crypto.subtle.sign('HMAC', key, encoder.encode(payload));
  const expectedHmac = Array.from(new Uint8Array(signature))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');

  // Constant-time comparison
  if (receivedHmac.length !== expectedHmac.length) return null;
  let mismatch = 0;
  for (let i = 0; i < receivedHmac.length; i++) {
    mismatch |= receivedHmac.charCodeAt(i) ^ expectedHmac.charCodeAt(i);
  }
  if (mismatch !== 0) return null;

  return username;
}

/**
 * Check if auth is enabled by scanning env vars for AUTH_USER_* keys.
 */
function isAuthEnabled(): boolean {
  for (const key of Object.keys(process.env)) {
    if (key.startsWith('AUTH_USER_') && process.env[key]) {
      return true;
    }
  }
  return false;
}

export async function middleware(request: NextRequest) {
  // If no AUTH_USER_* vars are set, auth is disabled — let everything through
  if (!isAuthEnabled()) {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;

  // Allow public paths without auth
  if (
    pathname === '/login' ||
    pathname.startsWith('/api/auth/') ||
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/favicon') ||
    pathname.endsWith('.ico') ||
    pathname.endsWith('.png') ||
    pathname.endsWith('.svg') ||
    pathname.endsWith('.jpg') ||
    pathname.endsWith('.css') ||
    pathname.endsWith('.js')
  ) {
    return NextResponse.next();
  }

  const token = request.cookies.get('session')?.value;
  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  const username = await validateSessionToken(token);
  if (!username) {
    // Clear invalid cookie and redirect
    const response = NextResponse.redirect(new URL('/login', request.url));
    response.cookies.set('session', '', { maxAge: 0, path: '/' });
    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon.ico (favicon)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
