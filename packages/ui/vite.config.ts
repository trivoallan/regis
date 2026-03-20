import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@regis-cli/ui": resolve(__dirname, "../../packages/ui/src"),
    },
  },
  build: {
    outDir: "dist",
    // Assets inlinés dans le HTML pour fonctionner sans serveur (artifact GitLab)
    assetsInlineLimit: 1024 * 1024, // 1MB — inline tout sauf les très gros chunks
    rollupOptions: {
      output: {
        // Nommage stable pour le cache Docker
        entryFileNames: "assets/viewer.[hash].js",
        chunkFileNames: "assets/vendor.[hash].js",
        assetFileNames: "assets/[name].[hash][extname]",
      },
    },
  },
});
