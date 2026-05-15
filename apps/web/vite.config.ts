// AegisCore student note: Vite build and development server configuration.

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiProxyTarget =
  process.env.VITE_DEV_PROXY_TARGET ?? "http://127.0.0.1:8000";

// Defines the frontend build and development server settings.
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, "")
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return undefined;
          }

          if (
            id.includes("recharts")
          ) {
            return "recharts";
          }

          if (
            id.includes("d3-") ||
            id.includes("victory-vendor")
          ) {
            return "chart-vendor";
          }

          return undefined;
        }
      }
    }
  }
});
