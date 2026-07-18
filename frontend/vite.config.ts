import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// GitHub Pages 仓库名：tomato_diease；本地开发 base 为 /
const base = process.env.GITHUB_PAGES === "true" ? "/tomato_diease/" : "/";

export default defineConfig({
  base,
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
      },
    },
  },
  build: {
    cssMinify: "esbuild",
  },
});
