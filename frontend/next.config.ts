import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The dev server is opened from this LAN address as well as localhost.
  allowedDevOrigins: ["192.168.1.183"],
};

export default nextConfig;
