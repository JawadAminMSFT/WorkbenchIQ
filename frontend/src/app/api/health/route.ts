import { NextResponse } from 'next/server';

export async function GET() {
  // Scan for AUTH_USER_* env vars
  const allKeys = Object.keys(process.env);
  const authKeys = allKeys.filter(k => k.toUpperCase().includes('AUTH'));
  // Show env var names containing APPSETTING (Azure sometimes prefixes)
  const appSettingKeys = allKeys.filter(k => k.includes('APPSETTING'));
  // Show a sample of env var names to understand the pattern
  const sampleKeys = allKeys.sort().slice(0, 30);
  
  return NextResponse.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    commitSha: process.env.NEXT_PUBLIC_COMMIT_SHA || 'unknown',
    debug: {
      authKeysFound: authKeys,
      appSettingKeysFound: appSettingKeys.slice(0, 10),
      hasAuthUser1: !!process.env.AUTH_USER_1,
      hasAppsettingAuthUser1: !!process.env.APPSETTING_AUTH_USER_1,
      envKeyCount: allKeys.length,
      sampleEnvKeys: sampleKeys,
    },
  });
}
