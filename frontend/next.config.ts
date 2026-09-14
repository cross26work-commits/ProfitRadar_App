import type { NextConfig } from "next";
import { backendOrigin } from "./config/backend-origin";

const nextConfig: NextConfig = {
  async rewrites() {
    const destinationOrigin = backendOrigin(process.env);
    return [
      {
        source: "/backend-api/:path*",
        destination: `${destinationOrigin}/:path*`,
      },
    ];
  },
};

export default nextConfig;
