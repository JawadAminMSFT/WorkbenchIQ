import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    commitSha: process.env.NEXT_PUBLIC_COMMIT_SHA || 'unknown',
  });
}
