// Prediction API service — communicates with the FastAPI + LLM + ML backend.

export interface PredictionRequest {
  district: string;
  built_up_area_sqft: number;
  plot_size_cents: number;
  bedrooms: number;
  bathrooms: number;
  floors: number;
  parking_spaces: number;
  balconies: number;
  kitchen_type: string;
  quality: string;
  roof_type: string;
  flooring: string;
  budget: number;
  addons: string[];
  site_description?: string;
}

export interface DetectedCondition {
  label: string;
  positive: boolean;
}

export interface SiteAnalysis {
  detected_conditions: DetectedCondition[];
  adjustment_percent: number; // e.g. -5 or +3
  adjustment_reason?: string;
  base_prediction: number;
  final_price: number;
  summary?: string;
}

export interface PredictionResponse {
  predicted_cost: number;
  cost_range: { min: number; max: number };
  model_accuracy: number;
  cost_per_sqft: number;
  house_category: string;
  construction_time: string;
  health_score: number;
  budget: { status: string; surplus: number; deficit: number; utilization: number };
  stage_breakdown: { stage: string; percentage: number; cost: number }[];
  recommendations: {
    type: string;
    title: string;
    description: string;
    priority: string;
    estimated_cost_impact: string;
  }[];
  addons: { selected: { name: string; cost: number }[]; total_cost: number };
  site_analysis?: SiteAnalysis;
}

const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

export async function predictPrice(
  payload: PredictionRequest
): Promise<PredictionResponse> {
  const res = await fetch(`${API_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => "");
    throw new Error(
      `Prediction backend error (${res.status}): ${errText || res.statusText}`
    );
  }

  return (await res.json()) as PredictionResponse;
}
