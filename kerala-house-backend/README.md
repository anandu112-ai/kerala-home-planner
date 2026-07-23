# Kerala House Price Prediction API

AI-powered construction cost estimation for Kerala properties.

**Stack:** FastAPI · Scikit-learn · Gemini / OpenAI LLM · Google Cloud Run

---

## Pipeline

```
User Input
    ↓
FastAPI /api/v1/predict
    ↓
ML Regression Model  →  base_prediction
    ↓
LLM Site Analysis    →  site features
    ↓
Price Adjustment Engine
    ↓
final_prediction + detected_conditions
```

---

## Project structure

```
kerala-house-backend/
├── main.py                          # FastAPI app + all routes
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .env.example
├── models/
│   └── house_model.pkl              # ← put your model here (not in Git)
└── services/
    ├── predictor.py                 # ML model loader + runner
    ├── llm_feature_extractor.py     # Gemini / OpenAI integration
    └── price_adjustment.py          # Rule-based adjustment engine
```

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Status check |
| GET | `/health` | Health + model loaded flag |
| POST | `/api/v1/predict` | Full prediction pipeline |

### POST /api/v1/predict — request

```json
{
  "district": "Ernakulam",
  "built_up_area_sqft": 1800,
  "plot_size_cents": 8,
  "bedrooms": 3,
  "bathrooms": 2,
  "floors": 2,
  "parking_spaces": 1,
  "balconies": 1,
  "kitchen_type": "Modular",
  "quality": "Standard",
  "roof_type": "Flat",
  "flooring": "Vitrified",
  "budget": 8000000,
  "addons": ["solar", "cctv"],
  "site_description": "Hilly area, no vehicle access, beautiful valley view, 1 km from main road"
}
```

### POST /api/v1/predict — response

```json
{
  "base_prediction": 7800000,
  "site_adjustment_amount": -156000,
  "site_adjustment_percentage": -2.0,
  "final_prediction": 7644000,
  "detected_conditions": [
    {
      "condition": "No vehicle access",
      "impact": -390000,
      "reason": "Accessibility difficulty reduces market value"
    },
    {
      "condition": "Beautiful scenic view",
      "impact": 390000,
      "reason": "Scenic advantage increases buyer demand and premium"
    },
    {
      "condition": "Hilly area",
      "impact": -156000,
      "reason": "Sloped terrain raises construction complexity and reduces valuation"
    }
  ],
  "model_accuracy": 96.0,
  "site_analysis_available": true
}
```

---

## 1 · Local development

### Prerequisites
- Python 3.11+
- `models/house_model.pkl` in place

```bash
cd kerala-house-backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY (or OPENAI_API_KEY)

# Start the server
uvicorn main:app --reload
```

Visit:
- API root: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## 2 · Docker (local)

```bash
cd kerala-house-backend

# Build the image
docker build -t kerala-house-backend .

# Run the container
docker run -p 8080:8080 \
  -e GEMINI_API_KEY=your_key_here \
  -e FRONTEND_URL=http://localhost:5173 \
  -v $(pwd)/models:/app/models \
  kerala-house-backend
```

> **Note:** The `-v` volume mount injects your local model file into the
> container. In production, bake the model into the image or use Cloud Storage.

Test it:
```bash
curl http://localhost:8080/health
curl http://localhost:8080/
```

---

## 3 · Google Cloud Run deployment

### Prerequisites
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and authenticated
- A GCP project with Cloud Run and Artifact Registry APIs enabled
- `models/house_model.pkl` present (copy it before building)

### Step 1 — Set project variables

```bash
export PROJECT_ID=your-gcp-project-id
export REGION=asia-south1          # Mumbai — closest to Kerala
export SERVICE=kerala-house-backend
export IMAGE=gcr.io/$PROJECT_ID/$SERVICE
```

### Step 2 — Authenticate

```bash
gcloud auth login
gcloud config set project $PROJECT_ID
gcloud auth configure-docker
```

### Step 3 — Build and push the image

```bash
cd kerala-house-backend

# Copy your model into place (if not already there)
# cp /path/to/house_model.pkl models/house_model.pkl

docker build -t $IMAGE .
docker push $IMAGE
```

Or use Cloud Build (no local Docker required):
```bash
gcloud builds submit --tag $IMAGE .
```

### Step 4 — Deploy to Cloud Run

```bash
gcloud run deploy $SERVICE \
  --image $IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars GEMINI_API_KEY=your_key_here,FRONTEND_URL=https://your-frontend.lovable.app
```

Cloud Run assigns a URL like:
```
https://kerala-house-backend-xxxxxxxxxx-em.a.run.app
```

### Step 5 — Update your frontend

Set `BACKEND_URL` (Railway) or `VITE_API_URL` (Vite build) to the Cloud Run URL above.

### Redeploy after code changes

```bash
docker build -t $IMAGE .
docker push $IMAGE
gcloud run deploy $SERVICE --image $IMAGE --region $REGION
```

---

## Environment variables reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | No* | — | Google Gemini API key |
| `OPENAI_API_KEY` | No* | — | OpenAI API key |
| `LLM_PROVIDER` | No | auto-detect | `"gemini"` or `"openai"` |
| `LLM_API_KEY` | No | — | Generic key (auto-detects provider) |
| `FRONTEND_URL` | No | `http://localhost:5173` | Allowed CORS origin |
| `MODEL_PATH` | No | `models/house_model.pkl` | Path to the .pkl file |

\* Without any LLM key the API still works — it returns the base ML prediction
with `site_analysis_available: false` and zero adjustment.

---

## Adjustment rules

| Condition | Adjustment |
|-----------|-----------|
| No vehicle access | −5 % |
| Poor road quality | −3 % |
| Hilly terrain | −2 % |
| Scenic view | +5 % |
| Good water supply | +2 % |
| Flood risk | −8 % |

Adjustments are **cumulative**. The ML model output is never modified.
