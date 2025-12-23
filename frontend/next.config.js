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
  
  // Rewrites to proxy API calls to backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
