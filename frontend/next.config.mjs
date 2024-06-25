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
};

export default nextConfig;
