/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
  // Docker 部署使用 standalone 输出
  output: 'standalone',
  webpack: (config) => {
    config.resolve.alias['@'] = path.join(__dirname, 'src');
    return config;
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  experimental: {
    // Prisma 需要外部打包（Next.js 14 用法）
    serverComponentsExternalPackages: ['@prisma/client', 'prisma'],
  },
};

module.exports = nextConfig;
