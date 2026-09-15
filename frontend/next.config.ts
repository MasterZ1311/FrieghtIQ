import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow images and other media from localhost backend
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "localhost", port: "8000" },
    ],
  },
};

export default nextConfig;
