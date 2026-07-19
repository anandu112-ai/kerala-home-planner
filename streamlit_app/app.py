"""
Kerala Home Cost Estimator — Streamlit App
==========================================
Loads the trained House_Model.pkl and provides a full interactive dashboard
with ML-predicted construction cost, budget analysis, stage breakdown,
scenario comparison and smart recommendations.
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Page config (MUST be first Streamlit call)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kerala Home Cost Estimator",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Custom CSS — premium dark-accent theme
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0f172a 0%, #1e3a8a 100%) !important;
    color: #f1f5f9 !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stNumberInput label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #f8fafc !important; }
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stNumberInput > div > div > input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
}

/* KPI metric cards */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
    border-radius: 16px;
    padding: 16px 20px;
    box-shadow: 0 4px 24px rgba(37,99,235,0.25);
    color: white !important;
}
div[data-testid="metric-container"] label { color: #bfdbfe !important; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: white !important; font-family: 'Plus Jakarta Sans', sans-serif; }
div[data-testid="metric-container"] div[data-testid="stMetricDelta"] { color: #86efac !important; }

/* Cards / expanders */
.stExpander { border-radius: 12px !important; border: 1px solid #e2e8f0 !important; }

/* Button */
.stButton > button {
    background: linear-gradient(90deg, #2563eb, #0ea5e9);
    color: white;
    border: none;
    border-radius: 999px;
    padding: 0.6rem 2rem;
    font-weight: 600;
    font-size: 0.95rem;
    transition: all 0.2s;
    width: 100%;
    box-shadow: 0 4px 14px rgba(37,99,235,0.35);
}
.stButton > button:hover { opacity: 0.92; transform: translateY(-1px); box-shadow: 0 6px 20px rgba(37,99,235,0.4); }

/* Section headers */
.section-header {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.4rem;
    font-weight: 800;
    color: #1e3a8a;
    margin-bottom: 0.5rem;
    border-left: 4px solid #2563eb;
    padding-left: 12px;
}
.sub-card {
    background: #f8fafc;
    border-radius: 14px;
    padding: 16px 20px;
    border: 1px solid #e2e8f0;
    margin-bottom: 10px;
}
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.badge-warning  { background:#fee2e2; color:#b91c1c; }
.badge-opt      { background:#fef3c7; color:#92400e; }
.badge-upgrade  { background:#dbeafe; color:#1d4ed8; }
.badge-positive { background:#dcfce7; color:#166534; }
.badge-risk     { background:#f1f5f9; color:#475569; }

.hero-banner {
    background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 60%, #0ea5e9 100%);
    border-radius: 20px;
    padding: 32px 36px;
    color: white;
    margin-bottom: 28px;
    box-shadow: 0 8px 32px rgba(37,99,235,0.3);
}
.hero-banner h1 { font-family: 'Plus Jakarta Sans',sans-serif; font-size: 2rem; font-weight: 800; margin: 0 0 6px 0; }
.hero-banner p  { color: #bfdbfe; margin: 0; font-size: 0.95rem; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Constants (mirrors backend/app/planner.py)
# ──────────────────────────────────────────────────────────────────────────────
DISTRICTS = [
    "Thiruvananthapuram", "Kollam", "Pathanamthitta", "Alappuzha",
    "Kottayam", "Idukki", "Ernakulam", "Thrissur", "Palakkad",
    "Malappuram", "Kozhikode", "Wayanad", "Kannur", "Kasaragod",
]

ADDON_OPTIONS = {
    "Compound Wall":  180000,
    "Gate":            45000,
    "Car Porch":      120000,
    "Borewell":        90000,
    "Septic Tank":     65000,
    "Solar Panels":   220000,
    "False Ceiling":  140000,
    "Interior Work":  350000,
    "Landscaping":     95000,
    "Smart Home":     180000,
    "CCTV":            55000,
}

STAGE_PERCENTAGES = {
    "Foundation": 12,
    "Structure":  30,
    "Roofing":    10,
    "Electrical":  8,
    "Plumbing":    8,
    "Flooring":   10,
    "Painting":    7,
    "Finishing":  15,
}

STAGE_COLORS = [
    "#1e3a8a", "#1d4ed8", "#2563eb", "#3b82f6",
    "#60a5fa", "#38bdf8", "#0ea5e9", "#0284c7",
]

QUALITY_OPTS   = ["Basic", "Standard", "Premium", "Luxury"]
KITCHEN_OPTS   = ["Normal", "Modular"]
ROOF_OPTS      = ["RCC", "Sloped Roof"]
FLOORING_OPTS  = ["Cement", "Vitrified Tile", "Granite", "Marble"]


# ──────────────────────────────────────────────────────────────────────────────
# Model loading (cached)
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading ML model…")
def load_model():
    # Look relative to this file → ../backend/models/House_Model.pkl
    base = Path(__file__).parent.parent / "backend" / "models" / "House_Model.pkl"
    if not base.exists():
        st.error(f"❌ Model not found at `{base}`. Make sure the file exists.")
        return None
    raw = joblib.load(base)
    if isinstance(raw, dict):
        return raw.get("model")
    return raw


# ──────────────────────────────────────────────────────────────────────────────
# Helper functions (mirrors backend logic)
# ──────────────────────────────────────────────────────────────────────────────
def fmt_inr(v: float) -> str:
    """Format a number as Indian Rupee string (₹X.XX L / Cr)."""
    if v >= 1e7:
        return f"₹{v/1e7:.2f} Cr"
    if v >= 1e5:
        return f"₹{v/1e5:.2f} L"
    return f"₹{v:,.0f}"


def predict_cost(model, inputs: dict) -> float:
    df = pd.DataFrame([{
        "district":          inputs["district"],
        "built_up_area_sqft": inputs["built_up_area"],
        "plot_size_cents":    inputs["plot_size"],
        "bedrooms":           inputs["bedrooms"],
        "bathrooms":          inputs["bathrooms"],
        "floors":             inputs["floors"],
        "parking_spaces":     inputs["parking"],
        "balconies":          inputs["balconies"],
        "kitchen_type":       inputs["kitchen"],
        "quality":            inputs["quality"],
        "roof_type":          inputs["roof"],
        "flooring":           inputs["flooring"],
    }])
    return round(float(model.predict(df)[0]), 2)


def stage_breakdown(base_cost: float) -> list[dict]:
    return [
        {"stage": s, "pct": p, "cost": round(base_cost * p / 100, 2)}
        for s, p in STAGE_PERCENTAGES.items()
    ]


def budget_analysis(predicted: float, budget: float) -> dict:
    util = round((predicted / budget) * 100, 1)
    if budget > predicted:
        return {"status": "Within Budget 🟢", "diff": budget - predicted,  "util": util, "color": "green"}
    if abs(predicted - budget) <= 200000:
        return {"status": "Budget Tight 🟡",  "diff": predicted - budget,  "util": util, "color": "orange"}
    return {"status": "Budget Short 🔴",      "diff": predicted - budget,  "util": util, "color": "red"}


def house_category(cost: float) -> str:
    if cost < 2_500_000: return "Budget House 🏠"
    if cost < 5_000_000: return "Standard House 🏡"
    if cost < 8_000_000: return "Premium House 🏘️"
    return "Luxury House 🏰"


def construction_time(area: float, floors: int) -> str:
    if area < 1200:   t = "5–6 Months"
    elif area < 1800: t = "6–8 Months"
    elif area < 2500: t = "8–10 Months"
    else:             t = "10–14 Months"
    return t + (" (Approx.)" if floors > 1 else "")


def health_score(predicted: float, budget: float, floors: int) -> int:
    s = 70
    if budget >= predicted:     s += 15
    if floors == 1:             s += 5
    if budget > predicted * 1.1: s += 10
    return min(s, 100)


def smart_recommendations(inputs: dict, predicted: float) -> list[dict]:
    recs = []
    budget = inputs["budget"]
    area   = inputs["built_up_area"]

    if budget >= predicted:
        recs.append({"badge":"positive","priority":"Low",
            "title":"Budget is Sufficient ✅",
            "desc":"Your available budget comfortably covers this project.",
            "impact":"No additional cost"})
        recs.append({"badge":"upgrade","priority":"Medium",
            "title":"Consider Solar Panels ☀️",
            "desc":"Long-term electricity savings and eco-friendly construction. Payback period ~6–8 years.",
            "impact":"₹2.20 L add-on"})
    else:
        recs.append({"badge":"warning","priority":"High",
            "title":"Budget Short ⚠️",
            "desc":f"You need {fmt_inr(predicted - budget)} more. Consider increasing budget or optimizing design.",
            "impact":"Depends on modifications"})
        if area > 1800:
            recs.append({"badge":"opt","priority":"High",
                "title":"Reduce Built-up Area",
                "desc":"Cutting 100–200 sqft can significantly lower cost without sacrificing liveability.",
                "impact":"Save ₹2–5 L"})
        if inputs["quality"] in ("Premium", "Luxury"):
            recs.append({"badge":"opt","priority":"Medium",
                "title":"Step Down Quality Tier",
                "desc":"Standard quality offers excellent durability at a fraction of the premium cost.",
                "impact":"Save ₹3–7 L"})
        if inputs["flooring"] in ("Granite", "Marble"):
            recs.append({"badge":"opt","priority":"Medium",
                "title":"Use Vitrified Tile Flooring",
                "desc":"Vitrified tiles give a premium look at significantly lower cost than granite/marble.",
                "impact":"Save ₹80K–1.5 L"})

    if inputs["floors"] > 2:
        recs.append({"badge":"risk","priority":"Medium",
            "title":"Multi-floor Structural Cost",
            "desc":f"{inputs['floors']} floors add significant structural load — ensure foundation design is certified.",
            "impact":"Extra ₹1.2 L per extra floor"})

    if "Solar Panels" in inputs.get("addons", []):
        recs.append({"badge":"positive","priority":"Low",
            "title":"Smart Choice: Solar Panels",
            "desc":"Great decision! You'll save ₹1,500–2,500/month on electricity bills.",
            "impact":"ROI in ~6 years"})

    if inputs["kitchen"] == "Modular":
        recs.append({"badge":"upgrade","priority":"Low",
            "title":"Modular Kitchen Selected",
            "desc":"Adds 6% to base cost but significantly improves functional value and resale price.",
            "impact":"+6% base cost"})

    return recs


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar — Inputs
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏡 Kerala Home Estimator")
    st.markdown("---")

    st.markdown("### 📍 Location")
    district = st.selectbox("District", DISTRICTS, index=DISTRICTS.index("Ernakulam"))

    st.markdown("### 🏠 House Specifications")
    built_up_area = st.slider("Built-up Area (sqft)", 500, 6000, 1800, 50)
    plot_size     = st.slider("Plot Size (cents)",       3,   50,    8,  1)
    bedrooms      = st.slider("Bedrooms",                1,    8,    3,  1)
    bathrooms     = st.slider("Bathrooms",               1,    8,    3,  1)
    floors        = st.slider("Floors",                  1,    4,    2,  1)

    st.markdown("### 🔧 Construction Details")
    parking   = st.slider("Parking Spaces", 0, 4, 1, 1)
    balconies = st.slider("Balconies",       0, 5, 2, 1)
    kitchen   = st.selectbox("Kitchen Type", KITCHEN_OPTS,  index=1)
    quality   = st.selectbox("Quality Tier", QUALITY_OPTS,  index=1)
    roof      = st.selectbox("Roof Type",    ROOF_OPTS,     index=0)
    flooring  = st.selectbox("Flooring",     FLOORING_OPTS, index=1)

    st.markdown("### 💰 Budget & Add-ons")
    budget = st.number_input("Available Budget (₹)", min_value=500_000, max_value=50_000_000,
                              value=5_500_000, step=100_000, format="%d")
    st.caption(fmt_inr(budget))

    addons = st.multiselect("Optional Add-ons", list(ADDON_OPTIONS.keys()))

    st.markdown("---")
    predict_btn = st.button("🔮 Predict Construction Cost", use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────
# Main area
# ──────────────────────────────────────────────────────────────────────────────
# Hero banner
st.markdown("""
<div class="hero-banner">
  <h1>🏡 Kerala Home Cost Estimator</h1>
  <p>ML-powered construction cost prediction for Kerala homes · Linear Regression · 14 Districts · R² 0.91</p>
</div>
""", unsafe_allow_html=True)

model = load_model()

if 'predicted' not in st.session_state:
    st.session_state.predicted = False

if predict_btn:
    st.session_state.predicted = True
    # Scroll to top of the page on button click
    st.components.v1.html(
        """
        <script>
            var body = window.parent.document.querySelector(".main");
            if (body) {
                body.scrollTo({top: 0, behavior: 'smooth'});
            } else {
                window.parent.scrollTo({top: 0, behavior: 'smooth'});
            }
        </script>
        """,
        height=0,
        width=0,
    )

if not st.session_state.predicted:
    # Welcome / instruction state
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Step 1** — Fill in location and house specifications in the sidebar.")
    with col2:
        st.info("**Step 2** — Set construction details, quality tier, and your budget.")
    with col3:
        st.info("**Step 3** — Click **Predict Construction Cost** to get your full dashboard.")
    st.stop()


if model is None:
    st.stop()

# ── Collect inputs ─────────────────────────────────────────────────────────
inputs = {
    "district":      district,
    "built_up_area": built_up_area,
    "plot_size":     plot_size,
    "bedrooms":      bedrooms,
    "bathrooms":     bathrooms,
    "floors":        floors,
    "parking":       parking,
    "balconies":     balconies,
    "kitchen":       kitchen,
    "quality":       quality,
    "roof":          roof,
    "flooring":      flooring,
    "budget":        budget,
    "addons":        addons,
}

addon_total   = sum(ADDON_OPTIONS.get(a, 0) for a in addons)
predicted_raw = predict_cost(model, inputs)
predicted     = predicted_raw + addon_total
base_cost     = predicted_raw
per_sqft      = round(base_cost / max(1, built_up_area), 0)
cost_range    = (round(predicted * 0.97), round(predicted * 1.03))
b_analysis    = budget_analysis(predicted, budget)
stages        = stage_breakdown(base_cost)
hs            = health_score(predicted, budget, floors)
category      = house_category(predicted)
c_time        = construction_time(built_up_area, floors)
recs          = smart_recommendations(inputs, predicted)

# ──────────────────────────────────────────────────────────────────────────────
# KPI Row
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">📊 Cost Summary</p>', unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
k1.metric("🏗️ Estimated Total Cost",  fmt_inr(predicted),
          delta=f"Base: {fmt_inr(base_cost)}")
k2.metric("📏 Cost per sqft",          f"₹{per_sqft:,.0f}")
k3.metric("⏱️ Construction Duration",  c_time)
k4.metric("🏠 House Category",         category.split(" ")[0] + " " + category.split(" ")[1])

st.divider()

# ──────────────────────────────────────────────────────────────────────────────
# Budget Analysis
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">💰 Budget Analysis</p>', unsafe_allow_html=True)

ba1, ba2, ba3 = st.columns([1, 1, 2])
with ba1:
    st.markdown(f"""
    <div class="sub-card">
      <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b">Your Budget</div>
      <div style="font-size:1.6rem;font-weight:800;color:#1e3a8a">{fmt_inr(budget)}</div>
    </div>
    <div class="sub-card">
      <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b">Predicted Cost</div>
      <div style="font-size:1.6rem;font-weight:800;color:#2563eb">{fmt_inr(predicted)}</div>
    </div>
    """, unsafe_allow_html=True)

with ba2:
    diff_label = "Surplus" if b_analysis["diff"] >= 0 and "Within" in b_analysis["status"] else "Deficit"
    diff_color = "#166534" if "Within" in b_analysis["status"] else "#b91c1c"
    st.markdown(f"""
    <div class="sub-card">
      <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b">{diff_label}</div>
      <div style="font-size:1.6rem;font-weight:800;color:{diff_color}">{fmt_inr(abs(b_analysis['diff']))}</div>
    </div>
    <div class="sub-card">
      <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b">Status</div>
      <div style="font-size:1.1rem;font-weight:700">{b_analysis['status']}</div>
      <div style="font-size:0.85rem;color:#64748b">Utilization: {b_analysis['util']}%</div>
    </div>
    """, unsafe_allow_html=True)

with ba3:
    util = min(b_analysis["util"], 120)
    bar_color = "#22c55e" if "Within" in b_analysis["status"] else ("#f59e0b" if "Tight" in b_analysis["status"] else "#ef4444")
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=b_analysis["util"],
        number={"suffix": "%", "font": {"size": 28, "color": "#1e3a8a"}},
        gauge={
            "axis": {"range": [0, 130], "tickwidth": 1, "tickcolor": "#94a3b8"},
            "bar":  {"color": bar_color, "thickness": 0.3},
            "bgcolor": "#f1f5f9",
            "steps": [
                {"range": [0,   90],  "color": "#dcfce7"},
                {"range": [90,  105], "color": "#fef9c3"},
                {"range": [105, 130], "color": "#fee2e2"},
            ],
            "threshold": {"line": {"color": "#1e3a8a", "width": 3}, "thickness": 0.7, "value": 100},
        },
        title={"text": "Budget Utilization", "font": {"size": 14, "color": "#64748b"}},
    ))
    gauge.update_layout(height=220, margin=dict(t=40, b=10, l=20, r=20), paper_bgcolor="white")
    st.plotly_chart(gauge, use_container_width=True, key="gauge")

st.divider()

# ──────────────────────────────────────────────────────────────────────────────
# Stage Breakdown + Pie
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">🧱 Construction Stage Breakdown</p>', unsafe_allow_html=True)

# Donut pie
pie = go.Figure(go.Pie(
    labels=[s["stage"] for s in stages],
    values=[s["cost"]  for s in stages],
    hole=0.55,
    marker=dict(colors=STAGE_COLORS, line=dict(color="white", width=2)),
    textinfo="label+percent",
    textfont=dict(size=12),
    hovertemplate="<b>%{label}</b><br>Cost: ₹%{value:,.0f}<br>%{percent}<extra></extra>",
))
pie.update_layout(
    showlegend=True,
    height=450,
    margin=dict(t=30, b=10, l=10, r=10),
    paper_bgcolor="white",
    annotations=[dict(
        text=f"<b>{fmt_inr(base_cost)}</b><br><span style='font-size:11px;color:#64748b'>Base cost</span>",
        x=0.5, y=0.5, font_size=16, showarrow=False
    )],
)
st.plotly_chart(pie, use_container_width=True, key="pie")

st.divider()

# ──────────────────────────────────────────────────────────────────────────────
# Add-ons Summary
# ──────────────────────────────────────────────────────────────────────────────
if addons:
    st.markdown('<p class="section-header">⚙️ Selected Add-ons</p>', unsafe_allow_html=True)
    addon_cols = st.columns(min(len(addons), 4))
    for i, a in enumerate(addons):
        with addon_cols[i % 4]:
            st.markdown(f"""
            <div class="sub-card" style="text-align:center">
              <div style="font-weight:700">{a}</div>
              <div style="color:#2563eb;font-weight:800;font-size:1.1rem">{fmt_inr(ADDON_OPTIONS[a])}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown(f"**Add-on Total:** {fmt_inr(addon_total)} &nbsp;·&nbsp; **Grand Total:** {fmt_inr(predicted)}")
    st.divider()

# ──────────────────────────────────────────────────────────────────────────────
# Scenario Comparison (quality tiers)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">📊 Quality Tier Scenario Comparison</p>', unsafe_allow_html=True)

QUALITY_FACTOR = {"Basic": 0.85, "Standard": 1.0, "Premium": 1.18, "Luxury": 1.4}
scenario_data = []
for q, f in QUALITY_FACTOR.items():
    sc_cost = round(predicted_raw * (f / QUALITY_FACTOR[quality]), 0) + addon_total
    scenario_data.append({"Quality": q, "Cost": sc_cost, "Selected": q == quality})

sc_df = pd.DataFrame(scenario_data)
sc_colors = ["#2563eb" if r["Selected"] else "#bfdbfe" for _, r in sc_df.iterrows()]

sc_chart = go.Figure(go.Bar(
    x=sc_df["Quality"], y=sc_df["Cost"],
    text=[fmt_inr(c) for c in sc_df["Cost"]],
    textposition="outside",
    marker=dict(color=sc_colors, line=dict(width=0)),
    marker_line_width=0,
))
sc_chart.update_layout(
    xaxis=dict(title=""),
    yaxis=dict(title="Total Cost (₹)", showgrid=True, gridcolor="#f1f5f9",
               tickformat=",.0f"),
    height=320,
    margin=dict(t=20, b=10, l=10, r=10),
    paper_bgcolor="white",
    plot_bgcolor="white",
    showlegend=False,
)
st.plotly_chart(sc_chart, use_container_width=True, key="scenario")
st.caption("Dark blue bar = your selected quality tier. All other inputs held constant.")

st.divider()

# ──────────────────────────────────────────────────────────────────────────────
# Smart Recommendations
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">💡 Smart Recommendations</p>', unsafe_allow_html=True)

BADGE_MAP = {
    "warning":  ("badge-warning",  "⚠️ Warning"),
    "opt":      ("badge-opt",      "🔧 Optimization"),
    "upgrade":  ("badge-upgrade",  "⬆️ Upgrade"),
    "positive": ("badge-positive", "✅ Positive"),
    "risk":     ("badge-risk",     "🔒 Risk"),
}
PRIORITY_COLOR = {"High": "#b91c1c", "Medium": "#d97706", "Low": "#166534"}

for r in recs:
    bclass, blabel = BADGE_MAP.get(r["badge"], ("badge-risk", r["badge"]))
    pcol = PRIORITY_COLOR.get(r["priority"], "#475569")
    with st.expander(f"{r['title']}  —  {r['priority']} priority", expanded=False):
        st.markdown(f"""
        <span class="badge {bclass}">{blabel}</span>
        &nbsp;
        <span style="font-size:0.75rem;font-weight:700;color:{pcol};background:{pcol}18;padding:2px 8px;border-radius:999px;border:1px solid {pcol}40">{r['priority']}</span>
        <p style="margin-top:10px;color:#334155">{r['desc']}</p>
        <div style="color:#2563eb;font-weight:600;font-size:0.9rem">💰 Impact: {r['impact']}</div>
        """, unsafe_allow_html=True)

st.divider()



# ── Footer ──────────────────────────────────────────────────────────────────
st.markdown("""
<hr style="margin-top:2rem;border-color:#e2e8f0">
<div style="text-align:center;color:#94a3b8;font-size:0.8rem;padding:1rem 0">
  Kerala Home Cost Estimator · ML-Powered · For planning reference only · R² 0.91
</div>
""", unsafe_allow_html=True)
