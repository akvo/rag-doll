import dotenv from "dotenv";
/** @type {import('next').NextConfig} */

const env = dotenv.config();
const backend_port = env.parsed.BACKEND_PORT;

const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "storage.googleapis.com",
      },
    ],
  },
};

export default nextConfig;
