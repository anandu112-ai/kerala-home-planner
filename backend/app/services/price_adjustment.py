import logging

logger = logging.getLogger("kerala_home_planner.services.price_adjustment")

# ---------------------------------------------------------------------------
# Construction Cost Adjustment Rules
# ---------------------------------------------------------------------------
# This engine adjusts the ML base prediction based on real-world site
# conditions that directly affect CONSTRUCTION COST — not resale value.
#
# Difficult site conditions increase cost because:
#   - No/poor vehicle access  → all materials must be head-loaded or
#                               transported by smaller vehicles; extra labour
#   - Poor road               → heavy vehicles (concrete mixer, crane) cannot
#                               reach; manual handling surcharge
#   - Hilly terrain           → deeper excavation, retaining walls, extra
#                               scaffolding, slope stabilisation
#   - Flood risk              → anti-flood foundation, waterproofing layers,
#                               elevated plinth, drainage systems
#   - Far from city           → material transportation cost + labour
#                               daily-travel or stay allowance
#
# Easy conditions can reduce cost:
#   - Good water availability → no need to bore well or hire water tankers
#                               during construction; curing cost drops
# ---------------------------------------------------------------------------

_RULES = [
    # (feature_key, feature_value, pct_change, label, reason)

    # ── Access & roads ──────────────────────────────────────────────────────
    (
        "vehicle_access", "none", +10.0,
        "No vehicle access",
        (
            "All materials must be head-loaded or carried manually. "
            "Labour cost surges significantly for material handling alone."
        ),
    ),
    (
        "vehicle_access", "poor", +5.0,
        "Poor vehicle access",
        (
            "Restricted vehicle entry means smaller trips and extra offloading "
            "labour, raising overall material-handling cost."
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
            "scaffolding and slope-stabilisation work — all add significant cost."
        ),
    ),

    # ── Risk factors ────────────────────────────────────────────────────────
    (
        "flood_risk", "yes", +6.0,
        "Flood risk area",
        (
            "Flood-prone sites require an elevated plinth, anti-flood "
            "foundation design, waterproofing layers and drainage channels."
        ),
    ),

    # ── Location ────────────────────────────────────────────────────────────
    (
        "distance_from_city", "high", +3.0,
        "Far from city",
        (
            "Remote locations increase material transportation cost and require "
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

    # ── Savings ─────────────────────────────────────────────────────────────
    (
        "water_availability", "good", -2.0,
        "Good water availability",
        (
            "Reliable on-site water supply eliminates the need for bore-well "
            "drilling or water-tanker hire during construction and curing."
        ),
    ),
]


def calculate_adjustments(base_price: float, features: dict) -> dict:
    """
    Apply site-condition rules to the ML base_price and return a full
    breakdown of detected conditions and their cost impact.

    Parameters
    ----------
    base_price : float
        ML model base prediction (rupees).
    features : dict
        Extracted site features from LLM (vehicle_access, terrain_type, etc.).

    Returns
    -------
    dict with keys:
        base_prediction            – original ML output, unchanged
        site_adjustment_amount     – total rupee delta (positive = cost increase)
        site_adjustment_percentage – cumulative % change
        final_prediction           – base + adjustment
        detected_conditions        – list of triggered rule dicts
    """
    total_pct = 0.0
    detected = []

    for feat_key, feat_val, pct, label, reason in _RULES:
        actual = features.get(feat_key)
        if actual is None:
            continue

        # Boolean comparison for boolean features; string for the rest
        if isinstance(feat_val, bool):
            match = actual is feat_val
        else:
            match = actual == feat_val

        if not match:
            continue

        impact = round(base_price * pct / 100.0, 2)
        total_pct += pct
        detected.append(
            {
                "condition": label,
                "impact": impact,       # positive = cost increase, negative = saving
                "reason": reason,
            }
        )
        logger.debug("Rule triggered: %s  (%+.1f%%,  impact ₹%.0f)", label, pct, impact)

    adjustment_amount = round(base_price * total_pct / 100.0, 2)
    final_price = max(0.0, round(base_price + adjustment_amount, 2))

    return {
        "base_prediction":            round(base_price, 2),
        "site_adjustment_amount":     adjustment_amount,
        "site_adjustment_percentage": round(total_pct, 2),
        "final_prediction":           final_price,
        "detected_conditions":        detected,
    }
