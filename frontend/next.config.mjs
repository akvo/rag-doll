import dotenv from "dotenv";
/** @type {import('next').NextConfig} */

dotenv.config();

const nextConfig = {
  output: "export",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://backend:5000/api/:path*", // Proxy to Backend
      },
    ];
  },
};

export default nextConfig;
