// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - TanStack devtools (dev-only, first), tanstackStart, viteReact, tailwindcss, tsConfigPaths,
//     nitro (build-only using cloudflare as a default target), VITE_* env injection, @ path alias,
//     React/TanStack dedupe, error logger plugins, and sandbox detection (port/host/strictPort).
// You can pass additional config via defineConfig({ vite: { ... }, etc... }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  tanstackStart: {
    // Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
    // nitro/vite builds from this
    server: { entry: "server" },
  },
  // Target a standalone Node server for Railway/self-hosted deployments.
  // `rollupConfig` disables internal-export mangling so the beta Nitro's
  // minifier doesn't rename `__commonJSMin` in the runtime chunk while leaving
  // importers referencing the original name (runtime TypeError otherwise).
  nitro: {
    preset: "node-server",
    rollupConfig: {
      output: { minifyInternalExports: false },
    },
  } as any,
});
