"""
services/price_adjustment.py
------------------------------
Pure rule-based engine that converts extracted site features into a price
adjustment on top of the ML base prediction.

Rules (cumulative, not exclusive):
  No vehicle access   → −5 %
  Poor road           → −3 %
  Hilly terrain       → −2 %
  Scenic view         → +5 %
  Good water supply   → +2 %
  Flood risk          → −8 %

The ML prediction is NEVER modified — the adjustment is calculated separately
and returned alongside the original base_prediction.
"""

import logging
from typing import Any

logger = logging.getLogger("kerala_house_backend.price_adjustment")

# ── Adjustment rules ────────────────────────────────────────────────────────
# Each rule: (feature_key, feature_value, pct_change, label, reason)
_RULES: list[tuple[str, Any, float, str, str]] = [
    (
        "vehicle_access", "none", -5.0,
        "No vehicle access",
        "Accessibility difficulty reduces market value",
    ),
    (
        "road_quality", "poor", -3.0,
        "Poor road",
        "Difficult road quality impacts approachability and resale",
    ),
    (
        "terrain_type", "hilly", -2.0,
        "Hilly area",
        "Sloped terrain raises construction complexity and reduces valuation",
    ),
    (
        "scenic_view", True, +5.0,
        "Beautiful scenic view",
        "Scenic advantage increases buyer demand and premium",
    ),
    (
        "water_availability", "good", +2.0,
        "Good water availability",
        "Reliable water supply adds premium value",
    ),
    (
        "flood_risk", "yes", -8.0,
        "Flood risk",
        "High vulnerability to seasonal floods significantly drops property worth",
    ),
]


def calculate_adjustments(base_price: float, features: dict) -> dict:
    """
    Apply site-condition rules to base_price.

    Returns
    -------
    dict with keys:
        base_prediction          – original ML output, unchanged
        site_adjustment_amount   – rupee delta (negative = reduction)
        site_adjustment_percentage – cumulative % (e.g. -7.0)
        final_prediction         – base + adjustment (floor 0)
        detected_conditions      – list of triggered rule details
    """
    total_pct = 0.0
    detected: list[dict] = []

    for feat_key, feat_val, pct, label, reason in _RULES:
        actual = features.get(feat_key)
        if actual is None:
            continue

        # Boolean comparison for scenic_view; string comparison for the rest
        match = (actual is feat_val) if isinstance(feat_val, bool) else (actual == feat_val)
        if not match:
            continue

        impact = round(base_price * pct / 100.0, 2)
        total_pct += pct
        detected.append(
            {
                "condition": label,
                "impact": impact,
                "reason": reason,
            }
        )
        logger.debug("Rule triggered: %s (%.1f%%)", label, pct)

    adjustment_amount = round(base_price * total_pct / 100.0, 2)
    final_price = max(0.0, round(base_price + adjustment_amount, 2))

    return {
        "base_prediction":          round(base_price, 2),
        "site_adjustment_amount":   adjustment_amount,
        "site_adjustment_percentage": round(total_pct, 2),
        "final_prediction":         final_price,
        "detected_conditions":      detected,
    }
