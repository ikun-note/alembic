/*
 * Description: Vite configuration: React + Tailwind v4 plugins, @ alias, dev proxy.
 *
 * Author: qinzhenya
 * Created: 2026-06-29
 */

import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  server: {
    // Dev proxy: frontend calls /api/* and reaches the FastAPI backend on :8000.
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
