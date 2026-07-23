// Server-side proxy for the FastAPI backend.
//
// Why this exists:
//   VITE_* variables are baked in at build time. On Railway/Vercel the build
//   runs before BACKEND_URL is known. Using a server function lets us read
//   process.env.BACKEND_URL at request time on the Node server.
//
// Error strategy:
//   The handler never throws — it returns { ok, data, error } so the client
//   can handle failures gracefully without an SSR page crash.

import { createServerFn } from "@tanstack/react-start";
import type { PredictionRequest, PredictionResponse } from "./predictionApi";

type ServerPredictResult =
  | { ok: true; data: PredictionResponse }
  | { ok: false; error: string };

function getBackendUrl(): string {
  const url = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
  return url.replace(/\/$/, "");
}

export const serverPredict = createServerFn({ method: "POST" })
  .validator((payload: PredictionRequest) => payload)
  .handler(async ({ data }): Promise<ServerPredictResult> => {
    const backendUrl = getBackendUrl();

    try {
      const res = await fetch(`${backendUrl}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        const errText = await res.text().catch(() => "");
        return {
          ok: false,
          error: `Backend error (${res.status}): ${errText || res.statusText}`,
        };
      }

      const json = (await res.json()) as PredictionResponse;
      return { ok: true, data: json };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { ok: false, error: message };
    }
  });

export const serverDownloadReport = createServerFn({ method: "GET" })
  .validator((predictionId: string) => predictionId)
  .handler(async ({ data: predictionId }): Promise<{ ok: true; pdfBase64: string } | { ok: false; error: string }> => {
    const backendUrl = getBackendUrl();
    try {
      const res = await fetch(`${backendUrl}/api/v1/report/${predictionId}`);
      if (!res.ok) {
        const errText = await res.text().catch(() => "");
        return {
          ok: false,
          error: `Backend error (${res.status}): ${errText || res.statusText}`,
        };
      }
      const arrayBuffer = await res.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      const pdfBase64 = buffer.toString("base64");
      return { ok: true, pdfBase64 };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { ok: false, error: message };
    }
  });

