/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_BLOCKCHAIN_RPC_URL: process.env.NEXT_PUBLIC_BLOCKCHAIN_RPC_URL || 'http://127.0.0.1:8545',
  },
}

module.exports = nextConfig
