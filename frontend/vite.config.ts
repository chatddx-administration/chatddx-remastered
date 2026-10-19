import { fileURLToPath } from "node:url";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [tailwindcss(), svelte()],
  resolve: {
    alias: { $lib: fileURLToPath(new URL("./src/lib", import.meta.url)) },
  },
  base: "/static/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        portal: "src/portal.css",
        home: "src/islands/home.ts",
        run: "src/islands/run.ts",
        thread: "src/islands/thread.ts",
        review: "src/islands/review.ts",
        translate: "src/islands/translate.ts",
        variation: "src/islands/variation.ts",
      },
    },
  },
});
