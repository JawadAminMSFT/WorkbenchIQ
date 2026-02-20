import { NextResponse } from 'next/server';

export async function GET() {
  // Scan for AUTH_USER_* env vars
  const authKeys = Object.keys(process.env).filter(k => k.startsWith('AUTH'));
  
  return NextResponse.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    commitSha: process.env.NEXT_PUBLIC_COMMIT_SHA || 'unknown',
    debug: {
      authKeysFound: authKeys,
      hasAuthUser1: !!process.env.AUTH_USER_1,
      authUser1Preview: process.env.AUTH_USER_1 ? process.env.AUTH_USER_1.substring(0, 5) + '...' : 'not set',
      hasAuthSecret: !!process.env.AUTH_SECRET,
      envKeyCount: Object.keys(process.env).length,
    },
  });
}
