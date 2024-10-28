import dotenv from "dotenv";
/** @type {import('next').NextConfig} */

const env = dotenv.config();
const backend_port = env.parsed.BACKEND_PORT;

const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `http://backend:${backend_port}/api/:path*`, // Proxy to Backend
      },
    ];
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "storage.googleapis.com",
      },
    ],
  },
  env: {
    NEXT_PUBLIC_VAPID_PUBLIC_KEY: process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY,
    NEXT_PUBLIC_VAPID_PRIVATE_KEY: process.env.NEXT_PUBLIC_VAPID_PRIVATE_KEY,
  },
};

export default nextConfig;
