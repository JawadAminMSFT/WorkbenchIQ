/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use standalone output for Azure Web App deployment
  output: 'standalone',
  
  // Extend timeout for API proxy (default is 30s, increase to 120s for LLM calls)
  httpAgentOptions: {
    keepAlive: true,
  },
  
  // Increase serverActions timeout
  experimental: {
    proxyTimeout: 120000, // 120 seconds
  },
  
  // API proxying is handled by API routes in src/app/api/[...path]/route.ts
  // This avoids build-time URL baking issues with rewrites
};

module.exports = nextConfig;
