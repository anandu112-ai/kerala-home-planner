import logging

logger = logging.getLogger("kerala_home_planner.services.price_adjustment")

try:
    from app.services.construction_cost_analyzer import calculate_construction_adjustments
except ImportError:
    from services.construction_cost_analyzer import calculate_construction_adjustments

# Rules for Site Condition Adjustments
# format: (feature_key, expected_value, percent_impact, condition_label, explanation)
SITE_RULES = [
    # Terrain Type
    ("terrain", "hilly", +8.0, "Hilly terrain", "Sloped/hilly sites require deeper excavation, retaining walls, and extra structural support."),
    ("terrain", "sloped", +4.0, "Sloped terrain", "Sloped terrain requires extra excavation and level filling."),

    # Vehicle Access
    ("vehicle_access", "none", +12.0, "No vehicle access", "No vehicle access requires manual head-loading of all construction materials."),
    ("vehicle_access", "poor", +6.0, "Poor vehicle access", "Poor/restricted vehicle access increases material-handling labour costs."),

    # Road Quality
    ("road_accessibility", "poor", +5.0, "Poor road quality", "Poor road quality limits heavy transit mixers and cranes, requiring manual workarounds."),
    ("road_accessibility", "average", +2.0, "Average road quality", "Narrow or single-lane roads slightly increase transit and delivery times."),

    # Location Advantage / Distance
    ("location_advantage", "negative", +4.0, "Remote location", "Remote location increases logistics, transport, and crew transit costs."),
    ("location_advantage", "positive", -3.0, "Location advantage", "Favourable location near highway/town reduces transport and mobilization costs."),

    # Scenic View
    ("scenic_view", True, +3.0, "Scenic view", "Scenic view or valley placements often require specialized structural framing and layouts."),

    # Flood Risk
    ("flood_risk", "high", +7.0, "High flood risk", "High flood risk requires elevated plinth beams and waterproofing/drainage infrastructure.")
]

def calculate_adjustments(base_price: float, features_data: dict) -> dict:
    """
    Applies construction and site adjustments to the ML model's base prediction.

    Parameters:
    - base_price: base ML prediction (float)
    - features_data: output from llm_feature_extractor containing:
        - corrected_text: normalized description string
        - detected_features: dictionary of extracted features
        - construction_features: dictionary of construction features
        - site_features: dictionary of site features

    Returns:
    - dict matching both current API and LLM output format specifications.
    """
    corrected_text = features_data.get("corrected_text", "")
    detected_features = features_data.get("detected_features", {})
    construction_features = features_data.get("construction_features", {})
    site_features = features_data.get("site_features", {})

    all_adjustments = []

    # 1. Calculate construction adjustments
    const_adj_amount, const_adjustments = calculate_construction_adjustments(base_price, construction_features)
    all_adjustments.extend(const_adjustments)

    # 2. Calculate site adjustments
    site_adj_pct = 0.0
    for feat_key, feat_val, pct, label, reason in SITE_RULES:
        actual = site_features.get(feat_key)
        if actual is None:
            continue

        # Comparison
        if isinstance(feat_val, bool):
            match = bool(actual) is feat_val
        else:
            match = str(actual).lower().strip() == feat_val

        if match:
            impact_amount = round(base_price * pct / 100.0, 2)
            site_adj_pct += pct
            all_adjustments.append({
                "condition": label,
                "feature": label,
                "impact": impact_amount,
                "amount": impact_amount,
                "reason": reason
            })
            logger.info("Site condition triggered: %s (%+.1f%%, ₹%.0f)", label, pct, impact_amount)

    site_adj_amount = round(base_price * site_adj_pct / 100.0, 2)

    # 3. Sum final prices
    # final_price = base_prediction + construction_adjustment + site_adjustment
    total_adjustment_amount = round(const_adj_amount + site_adj_amount, 2)
    final_price = max(0.0, round(base_price + total_adjustment_amount, 2))
    total_percentage = round((total_adjustment_amount / base_price) * 100.0, 2) if base_price > 0 else 0.0

    logger.info("Base Price: ₹%.2f, Construction Adj: ₹%.2f, Site Adj: ₹%.2f, Final: ₹%.2f",
                base_price, const_adj_amount, site_adj_amount, final_price)

    # Return structure compatible with the frontend expectations AND new requirements:
    return {
        "base_prediction": round(base_price, 2),
        "site_adjustment_amount": total_adjustment_amount,
        "site_adjustment_percentage": total_percentage,
        "final_prediction": final_price,
        "detected_conditions": all_adjustments,
        # Extended fields for the new LLM output format
        "corrected_text": corrected_text,
        "detected_features": detected_features,
        "adjustments": all_adjustments
    }
