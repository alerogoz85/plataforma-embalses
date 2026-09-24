import type { NextConfig } from "next";

// URL del backend (proyecto de API en Vercel). Si se define, el sitio reenvia
// /api/v1/* hacia alli: el navegador solo habla con el dominio del sitio, sin CORS.
const API_URL = process.env.API_URL?.replace(/\/+$/, "");

const nextConfig: NextConfig = {
  async rewrites() {
    return API_URL ? [{ source: "/api/v1/:path*", destination: `${API_URL}/api/v1/:path*` }] : [];
  },
};

export default nextConfig;
