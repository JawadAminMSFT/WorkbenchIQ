import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    // Forward query parameters to backend
    const searchParams = request.nextUrl.searchParams;
    const queryString = searchParams.toString();
    const url = queryString 
      ? `${API_BASE_URL}/api/applications?${queryString}`
      : `${API_BASE_URL}/api/applications`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (process.env.API_KEY) {
      headers['X-API-Key'] = process.env.API_KEY;
    }

    const response = await fetch(url, {
      headers,
      cache: 'no-store',
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to fetch applications:', error);
    
    // Return demo data for development
    return NextResponse.json([
      {
        id: '3c0452c0',
        created_at: '2025-11-25T17:40:26Z',
        external_reference: 'UW-004',
        status: 'completed',
        summary_title: 'Mike Johnson - APS Review',
      },
    ]);
  }
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    
    const postHeaders: Record<string, string> = {};
    if (process.env.API_KEY) {
      postHeaders['X-API-Key'] = process.env.API_KEY;
    }

    const response = await fetch(`${API_BASE_URL}/api/applications`, {
      method: 'POST',
      headers: postHeaders,
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to create application:', error);
    return NextResponse.json(
      { error: 'Failed to create application' },
      { status: 500 }
    );
  }
}
