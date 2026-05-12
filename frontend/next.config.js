/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable Turbopack for CPU compatibility
  // Using Babel/Webpack instead
  experimental: {
    // Disable turbopack for older CPU compatibility
  }
}

module.exports = nextConfig
