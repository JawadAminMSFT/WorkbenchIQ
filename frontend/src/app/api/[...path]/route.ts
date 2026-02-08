import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.API_URL || 'http://localhost:8000';

/**
 * Catch-all API route that proxies unhandled requests to the backend.
 * This ensures all /api/* requests are forwarded to the Python backend.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path);
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'POST');
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'PUT');
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'DELETE');
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'PATCH');
}

async function proxyRequest(
  request: NextRequest,
  pathSegments: string[],
  method?: string
) {
  try {
    const path = pathSegments.join('/');
    const searchParams = request.nextUrl.searchParams;
    const queryString = searchParams.toString();
    const url = queryString
      ? `${API_BASE_URL}/api/${path}?${queryString}`
      : `${API_BASE_URL}/api/${path}`;

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const fetchOptions: RequestInit = {
      method: method || request.method,
      headers,
      cache: 'no-store',
    };

    // Forward body for non-GET requests
    if (method && method !== 'GET') {
      try {
        const contentType = request.headers.get('content-type') || '';
        if (contentType.includes('multipart/form-data')) {
          // For form data, forward as-is
          const formData = await request.formData();
          delete (headers as Record<string, string>)['Content-Type'];
          fetchOptions.body = formData;
        } else {
          // For JSON, forward body
          const body = await request.text();
          if (body) {
            fetchOptions.body = body;
          }
        }
      } catch {
        // No body to forward
      }
    }

    const response = await fetch(url, fetchOptions);

    // Handle non-JSON responses
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      const data = await response.json();
      return NextResponse.json(data, { status: response.status });
    } else {
      const text = await response.text();
      return new NextResponse(text, {
        status: response.status,
        headers: { 'Content-Type': contentType },
      });
    }
  } catch (error) {
    console.error('API proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to proxy request to backend' },
      { status: 500 }
    );
  }
}
