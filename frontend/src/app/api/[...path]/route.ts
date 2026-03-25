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

    // Inject API key for backend authentication (server-side only, never exposed to browser)
    const apiKey = process.env.API_KEY;
    if (apiKey) {
      (headers as Record<string, string>)['X-API-Key'] = apiKey;
    }

    // Forward Range header for video/audio streaming (HTTP 206 Partial Content)
    const rangeHeader = request.headers.get('range');
    if (rangeHeader) {
      (headers as Record<string, string>)['Range'] = rangeHeader;
    }

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
      // For binary content (PDFs, images, video), use arrayBuffer to
      // preserve bytes. Using response.text() corrupts binary data and
      // causes browsers to show "password protected" for PDFs.
      const isBinary = /^(application\/(pdf|octet-stream)|image\/|video\/|audio\/)/.test(contentType);
      if (isBinary) {
        const buffer = await response.arrayBuffer();
        const responseHeaders: Record<string, string> = {
          'Content-Type': contentType,
        };
        const contentLength = response.headers.get('content-length');
        if (contentLength) responseHeaders['Content-Length'] = contentLength;
        const contentDisposition = response.headers.get('content-disposition');
        if (contentDisposition) responseHeaders['Content-Disposition'] = contentDisposition;
        const acceptRanges = response.headers.get('accept-ranges');
        if (acceptRanges) responseHeaders['Accept-Ranges'] = acceptRanges;
        const contentRange = response.headers.get('content-range');
        if (contentRange) responseHeaders['Content-Range'] = contentRange;
        return new NextResponse(buffer, {
          status: response.status,
          headers: responseHeaders,
        });
      }
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
