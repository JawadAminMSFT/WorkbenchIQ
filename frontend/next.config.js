/** @type {import('next').NextConfig} */
const nextConfig = {
  // Extend timeout for API proxy (default is 30s, increase to 120s for LLM calls)
  httpAgentOptions: {
    keepAlive: true,
  },
  
  // Increase serverActions timeout
  experimental: {
    proxyTimeout: 120000, // 120 seconds
  },

  // Expose API_URL to the browser bundle as NEXT_PUBLIC_API_URL
  // so we don't need to set a separate NEXT_PUBLIC_ env var in Azure
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || process.env.API_URL || '',
  },
  
  // Rewrites to proxy API calls to backend
  // Uses API_URL env var in production, falls back to localhost for local dev
  async rewrites() {
    const backendUrl = process.env.API_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
