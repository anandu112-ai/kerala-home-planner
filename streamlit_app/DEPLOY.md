# 🚀 Streamlit Deployment Guide

This guide explains how to deploy the Kerala Home Cost Estimator as a **Streamlit Community Cloud** app (free, no server needed).

---

## 📁 What's in this folder

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application |
| `requirements.txt` | Python dependencies for Streamlit Cloud |
| `.streamlit/config.toml` | Theme & server configuration |

---

## ☁️ Deploy to Streamlit Community Cloud (Free)

### Prerequisites
- A GitHub account (project already pushed ✅)
- A free account at [share.streamlit.io](https://share.streamlit.io)

### Steps

1. **Go to [share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub.

2. Click **"New app"**.

3. Fill in the form:
   | Field | Value |
   |-------|-------|
   | **Repository** | `anandu112-ai/kerala-home-planner` |
   | **Branch** | `main` |
   | **Main file path** | `streamlit_app/app.py` |

4. Click **"Deploy!"** — Streamlit Cloud will automatically use `streamlit_app/requirements.txt`.

5. Your app will be live at:  
   `https://<your-username>-kerala-home-planner.streamlit.app`

> **Note:** The ML model (`backend/models/House_Model.pkl`) is included in the repository, so Streamlit Cloud can access it directly via the relative path `../backend/models/House_Model.pkl`.

---

## 💻 Run Locally

```bash
# From the project root:
pip install -r streamlit_app/requirements.txt
streamlit run streamlit_app/app.py
```

The app opens at [http://localhost:8501](http://localhost:8501).

---

## 🧩 App Features

| Feature | Description |
|---------|-------------|
| 📊 KPI Dashboard | Estimated cost, range, duration, category, accuracy |
| 💰 Budget Gauge | Interactive Plotly gauge showing utilization % |
| 🧱 Stage Breakdown | Donut pie + horizontal bar for 8 construction stages |
| 📊 Scenario Comparison | Bar chart across Basic / Standard / Premium / Luxury |
| 💡 Smart Recommendations | Expandable cards with priority tags and cost impact |
| ⚙️ Add-ons Panel | All selected add-ons with individual and total cost |
| 📋 Configuration Summary | Full summary of all input parameters |

---

## 🔧 Architecture

```
User → Streamlit Sidebar (inputs)
     → Loads House_Model.pkl directly via joblib
     → Runs sklearn predict() locally
     → Renders Plotly charts + Streamlit components
```

No external API calls are made — the model runs **100% client-side** on the Streamlit server.
