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

  // Expose API_URL to the browser bundle as NEXT_PUBLIC_API_URL
  // so we don't need to set a separate NEXT_PUBLIC_ env var in Azure
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || process.env.API_URL || '',
  },
  
  // API proxying is handled by API routes in src/app/api/[...path]/route.ts
  // This avoids build-time URL baking issues with rewrites
};

module.exports = nextConfig;
