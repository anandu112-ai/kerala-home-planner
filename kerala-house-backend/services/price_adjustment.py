"""
services/price_adjustment.py
------------------------------
Rule-based engine that adjusts the ML base construction cost prediction
based on real-world SITE CONDITIONS that affect CONSTRUCTION COST.

This is NOT a property resale value model.
Difficult site conditions raise construction cost because:
  - No/poor vehicle access  → head-loading and manual material handling
  - Poor road               → heavy vehicles cannot reach; extra handling
  - Hilly terrain           → excavation, retaining walls, scaffolding
  - Flood risk              → elevated plinth, waterproofing, drainage
  - Remote location         → transport cost + crew travel allowance

Easy conditions can save cost:
  - Good water availability → no bore-well or water-tanker needed

The ML base_prediction is NEVER modified — adjustment is computed separately.
"""

import logging
from typing import Any

logger = logging.getLogger("kerala_house_backend.price_adjustment")

# ── Adjustment rules ────────────────────────────────────────────────────────
# Each tuple: (feature_key, feature_value, pct_change, label, reason)
# pct_change > 0  → construction cost INCREASES
# pct_change < 0  → construction cost DECREASES (saving)
_RULES: list[tuple[str, Any, float, str, str]] = [

    # ── Access & roads ──────────────────────────────────────────────────────
    (
        "vehicle_access", "none", +10.0,
        "No vehicle access",
        (
            "All materials must be head-loaded or hand-carried to the site. "
            "Labour cost surges significantly for material handling alone."
        ),
    ),
    (
        "vehicle_access", "poor", +5.0,
        "Poor vehicle access",
        (
            "Restricted vehicle entry means smaller loads per trip and extra "
            "offloading labour, raising overall material-handling cost."
        ),
    ),
    (
        "road_quality", "poor", +4.0,
        "Poor road quality",
        (
            "Heavy construction vehicles (concrete mixers, cranes, tippers) "
            "cannot access freely; extra handling and detour costs apply."
        ),
    ),

    # ── Terrain ─────────────────────────────────────────────────────────────
    (
        "terrain_type", "hilly", +7.0,
        "Hilly terrain",
        (
            "Sloped sites need deeper excavation, retaining walls, extra "
            "scaffolding and slope-stabilisation — all add significant cost."
        ),
    ),

    # ── Risk factors ────────────────────────────────────────────────────────
    (
        "flood_risk", "yes", +6.0,
        "Flood risk area",
        (
            "Flood-prone sites require elevated plinth, anti-flood foundation "
            "design, waterproofing layers and drainage channel construction."
        ),
    ),

    # ── Location / remoteness ───────────────────────────────────────────────
    (
        "distance_from_city", "high", +3.0,
        "Far from city",
        (
            "Remote sites increase material transportation cost and require "
            "daily travel or accommodation allowance for the construction crew."
        ),
    ),
    (
        "distance_from_city", "medium", +1.5,
        "Moderate distance from city",
        (
            "Moderate distance slightly raises transportation and "
            "crew travel costs."
        ),
    ),

    # ── Cost savings ────────────────────────────────────────────────────────
    (
        "water_availability", "good", -2.0,
        "Good water availability",
        (
            "Reliable on-site water eliminates bore-well drilling and "
            "water-tanker hire during construction and curing stages."
        ),
    ),
]


def calculate_adjustments(base_price: float, features: dict) -> dict:
    """
    Apply site-condition rules to base_price.

    Returns
    -------
    dict with keys:
        base_prediction            – original ML output, unchanged
        site_adjustment_amount     – total rupee delta (positive = more expensive)
        site_adjustment_percentage – cumulative % change
        final_prediction           – base + adjustment (floored at 0)
        detected_conditions        – list of triggered rule dicts
    """
    total_pct = 0.0
    detected: list[dict] = []

    for feat_key, feat_val, pct, label, reason in _RULES:
        actual = features.get(feat_key)
        if actual is None:
            continue

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
        logger.debug("Rule triggered: %s  (%+.1f%%,  ₹%.0f)", label, pct, impact)

    adjustment_amount = round(base_price * total_pct / 100.0, 2)
    final_price = max(0.0, round(base_price + adjustment_amount, 2))

    return {
        "base_prediction":            round(base_price, 2),
        "site_adjustment_amount":     adjustment_amount,
        "site_adjustment_percentage": round(total_pct, 2),
        "final_prediction":           final_price,
        "detected_conditions":        detected,
    }
