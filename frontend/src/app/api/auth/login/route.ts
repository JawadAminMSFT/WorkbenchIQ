import { NextRequest, NextResponse } from 'next/server';
import { getUsers, createSessionToken, isAuthEnabled } from '@/lib/auth';

export async function POST(request: NextRequest) {
  // If auth is not configured, reject
  if (!isAuthEnabled()) {
    return NextResponse.json(
      { error: 'Authentication is not configured. Set AUTH_USER_* environment variables.' },
      { status: 503 }
    );
  }

  try {
    const { username, password } = await request.json();

    if (!username || !password) {
      return NextResponse.json({ error: 'Username and password are required' }, { status: 400 });
    }

    const users = getUsers();
    const storedPassword = users.get(username);

    if (!storedPassword || storedPassword !== password) {
      return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    }

    // Create session token and set cookie
    const token = createSessionToken(username);
    const isProduction = process.env.NODE_ENV === 'production';

    const response = NextResponse.json({ username });
    response.cookies.set('session', token, {
      httpOnly: true,
      secure: isProduction,
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60 * 24, // 24 hours
    });

    return response;
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }
}
