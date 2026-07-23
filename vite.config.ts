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
  nitro: {
    preset: "node-server",

    // --- Fix: TypeError: __commonJSMin is not a function ---
    //
    // Rolldown (Vite 8's bundler) splits the SSR output into multiple chunks.
    // CJS packages (react-query, use-sync-external-store/shim, etc.) get a
    // `__commonJSMin` helper hoisted into ONE chunk. Caller chunks in separate
    // files end up referencing an undefined `__commonJSMin` → runtime TypeError.
    //
    // Fix 1: disable internal-export mangling so helpers aren't renamed/moved.
    rollupConfig: {
      output: { minifyInternalExports: false },
    },

    // Fix 2: force Nitro to inline (bundle) the problematic CJS packages into
    // the server entry instead of letting Rolldown split them into external
    // chunks that lose the `__commonJSMin` wrapper reference.
    bundledStorage: [],
    serverAssets: [],
    inlineDynamicImports: true,
  } as any,
});
