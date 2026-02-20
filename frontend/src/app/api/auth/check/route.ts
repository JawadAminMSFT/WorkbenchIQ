import { NextRequest, NextResponse } from 'next/server';
import { validateSessionToken, isAuthEnabled } from '@/lib/auth';

export async function GET(request: NextRequest) {
  // If no auth configured, return as if authenticated (auth disabled)
  if (!isAuthEnabled()) {
    return NextResponse.json({ authenticated: true, authEnabled: false });
  }

  const token = request.cookies.get('session')?.value;
  if (!token) {
    return NextResponse.json({ authenticated: false, authEnabled: true }, { status: 401 });
  }

  const username = validateSessionToken(token);
  if (!username) {
    return NextResponse.json({ authenticated: false, authEnabled: true }, { status: 401 });
  }

  return NextResponse.json({ authenticated: true, authEnabled: true, username });
}
