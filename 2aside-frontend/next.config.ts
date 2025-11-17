import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Disable dev indicators and error overlays
  devIndicators: {
    buildActivity: false,
    buildActivityPosition: 'bottom-right',
  },
  // Override webpack config to disable error overlay
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      // Disable error overlay by removing the plugin
      config.plugins = config.plugins.filter(
        (plugin: any) => plugin.constructor.name !== 'ReactRefreshPlugin'
      );
    }
    return config;
  },
};

export default nextConfig;
