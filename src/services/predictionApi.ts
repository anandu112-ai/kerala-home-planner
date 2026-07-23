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

// Matches backend DetectedCondition schema
export interface DetectedCondition {
  condition: string;   // e.g. "No vehicle access"
  impact: number;      // rupee delta, negative = reduction e.g. -400000
  reason: string;      // e.g. "Accessibility difficulty reduces market value"
}

// Matches backend SiteAdjustment schema (returned inside site_analysis)
export interface SiteAnalysis {
  base_prediction: number;
  site_adjustment_amount: number;      // rupee delta e.g. -150000
  site_adjustment_percentage: number;  // e.g. -2.0
  final_prediction: number;
  detected_conditions: DetectedCondition[];
}

export interface SimilarProperty {
  district: string;
  location: string;
  built_up_area_sqft: number;
  bedrooms: number;
  quality: string;
  price: number;
  similarity: number;
}

export interface MarketAnalysis {
  average_price: number;
  lowest_price: number;
  highest_price: number;
  price_difference: number;
  position: string;
}

export interface PredictionResponse {
  predicted_cost: number;
  predicted_price: number;
  prediction_id: string;
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
  // Present when site_description was provided and LLM succeeded
  site_analysis?: SiteAnalysis | null;
  // Similar properties & market statistics
  similar_properties?: SimilarProperty[];
  market_analysis?: MarketAnalysis | null;
  ai_explanation?: string;
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
