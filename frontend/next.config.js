/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',     // Quan trọng cho Docker
  reactStrictMode: true,
  images: {
    unoptimized: true,      // Quan trọng khi deploy Docker
  },
};

export default nextConfig;