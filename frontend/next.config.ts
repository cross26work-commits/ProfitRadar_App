import type { NextConfig } from "next";
import { backendOrigin } from "./config/backend-origin";
import { validatePublication } from "./config/publication";

validatePublication(process.env);

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
