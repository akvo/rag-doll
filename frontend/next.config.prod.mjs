import dotenv from "dotenv";
/** @type {import('next').NextConfig} */

const env = dotenv.config();
const backend_port = env.parsed.BACKEND_PORT;

const nextConfig = {
};

export default nextConfig;