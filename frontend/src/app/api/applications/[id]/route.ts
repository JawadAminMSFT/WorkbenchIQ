import { NextRequest, NextResponse } from 'next/server';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

const API_BASE_URL = process.env.API_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const appId = params.id;
  
  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (process.env.API_KEY) {
      headers['X-API-Key'] = process.env.API_KEY;
    }

    const response = await fetch(`${API_BASE_URL}/api/applications/${appId}`, {
      headers,
      cache: 'no-store',
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error(`Failed to fetch application ${appId}:`, error);
    
    // Try to load from local data directory for demo purposes
    try {
      const metadataPath = join(
        process.cwd(),
        '..',
        'data',
        'applications',
        appId,
        'metadata.json'
      );
      
      if (existsSync(metadataPath)) {
        const metadata = JSON.parse(readFileSync(metadataPath, 'utf-8'));
        return NextResponse.json(metadata);
      }
    } catch (localError) {
      console.error('Local data load failed:', localError);
    }

    return NextResponse.json(
      { error: 'Application not found' },
      { status: 404 }
    );
  }
}
