// Server-side proxy for the FastAPI backend.
//
// Why this exists:
//   VITE_* variables are baked in at build time. On Railway the build runs
//   before BACKEND_URL is known (or it's set as a runtime env var, not a
//   build-time VITE_ var). Using a server function lets us read BACKEND_URL
//   at request time on the Node server, so Railway deployments Just Work.
//
// The frontend calls this server function instead of hitting the FastAPI
// backend directly. The Node server forwards the request with the correct URL.

import { createServerFn } from "@tanstack/react-start";
import type { PredictionRequest, PredictionResponse } from "./predictionApi";

// Resolve backend URL at runtime (server side only).
function getBackendUrl(): string {
  // process.env is available server-side in TanStack Start / Nitro Node preset.
  const url = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
  return url.replace(/\/$/, "");
}

export const serverPredict = createServerFn({ method: "POST" })
  .validator((payload: PredictionRequest) => payload)
  .handler(async ({ data }) => {
    const backendUrl = getBackendUrl();

    const res = await fetch(`${backendUrl}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const errText = await res.text().catch(() => "");
      throw new Error(
        `Backend error (${res.status}): ${errText || res.statusText}`
      );
    }

    return (await res.json()) as PredictionResponse;
  });
