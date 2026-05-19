import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8110",
        changeOrigin: true,
      },
      "/v1": {
        target: "http://localhost:8101",
        changeOrigin: true,
      },
    },
  },
});
