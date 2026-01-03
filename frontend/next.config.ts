import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/t/:threadId',
        destination: '/thread/:threadId',
      },
    ];
  },
};

export default nextConfig;
