import logging

logger = logging.getLogger("kerala_home_planner.services.construction_cost_analyzer")

# Rules for Construction Cost Adjustments
# format: (feature_key, expected_value, percent_impact, condition_label, explanation_template)
CONSTRUCTION_RULES = [
    # Material Quality
    ("material_quality", "luxury", +10.0, "Luxury materials", "Ultra-high-end material selection (imported fittings, structural enhancements) increases baseline cost."),
    ("material_quality", "premium", +6.0, "Premium materials", "High-grade materials (reputed brands for cement, steel, paint) increase overall construction durability and cost."),
    ("material_quality", "basic", -5.0, "Basic materials", "Use of economy-grade structural and finishing materials reduces base construction cost."),

    # Flooring Quality
    ("flooring_quality", "luxury", +8.0, "Luxury flooring (Marble/Granite)", "Upgrading to luxury marble or granite flooring significantly increases material and specialized laying labour cost."),
    ("flooring_quality", "premium", +4.0, "Premium flooring (Vitrified/Granite)", "Premium flooring selection (high-quality vitrified tiles or partial granite) increases material value."),
    ("flooring_quality", "basic", -2.0, "Basic flooring", "Using standard ceramic tiles or basic cement flooring lowers finish costs."),

    # Wood Work Quality
    ("wood_work_quality", "premium", +7.0, "Premium teak/hardwood work", "Premium hardwood/teak woodwork for doors, windows, and panels increases artisan labour and material cost."),
    ("wood_work_quality", "standard", +3.0, "Standard woodwork", "Standard hardwood woodwork for internal fittings moderately increases construction cost."),

    # Kitchen Specification
    ("kitchen_specification", "premium_modular", +6.0, "Premium modular kitchen", "High-end modular kitchen with premium cabinetry, chimney, hob, and quartz/granite countertop."),
    ("kitchen_specification", "modular", +3.5, "Standard modular kitchen", "Standard modular kitchen cabinets and counter setup adds to construction cost."),

    # Bathroom Quality
    ("bathroom_quality", "premium", +3.0, "Premium sanitaryware", "Upgraded premium bathroom fixtures, concealed plumbing, and high-end tiling."),
    ("bathroom_quality", "basic", -2.0, "Basic sanitaryware", "Simple economy sanitaryware and standard plumbing layouts."),

    # Electrical Work
    ("electrical_work", "premium", +3.0, "Premium electrical & automation", "Premium wiring, smart switches, 3-phase connection, or basic automation features."),

    # Construction Grade
    ("construction_grade", "luxury", +12.0, "Luxury construction grade", "Elite luxury grade construction including architect fees, premium structural design, and superior finishes."),
    ("construction_grade", "premium", +6.0, "Premium construction grade", "Premium grade construction with superior framing, reinforced concrete, and professional supervision.")
]

# Fixed amount / percentage additions for specific premium features
PREMIUM_ADDONS_RULES = {
    "solar": (+3.0, "On-site solar panel system", "Installation of a grid-tied solar power system (adds to initial construction budget)."),
    "pool": (+10.0, "Private swimming pool", "Excavation, waterproofing, filtration systems, and finishing for a private pool add significant cost."),
    "automation": (+4.0, "Smart home automation", "Smart home hub, security sensors, motorized curtain tracks, and automated lighting system."),
    "landscaping": (+3.0, "Premium landscaping & garden", "Professional garden design, lawns, paving stones, and outdoor water features.")
}

def calculate_construction_adjustments(base_price: float, features: dict) -> tuple[float, list[dict]]:
    """
    Computes cost adjustments specifically caused by construction materials,
    flooring, woodwork, kitchen specs, electrical, grade, and premium addons.

    Parameters:
    - base_price: the ML model's base prediction (float)
    - features: the extracted construction_features dictionary

    Returns:
    - tuple: (total_construction_adjustment_amount, list_of_triggered_adjustments)
    """
    total_pct = 0.0
    adjustments_list = []
    
    # Process categorical construction rules
    for feat_key, feat_val, pct, label, reason in CONSTRUCTION_RULES:
        actual = features.get(feat_key)
        if actual and str(actual).lower().strip() == feat_val:
            impact_amount = round(base_price * pct / 100.0, 2)
            total_pct += pct
            adjustments_list.append({
                "condition": label,
                "feature": label,
                "impact": impact_amount,
                "amount": impact_amount,
                "reason": reason
            })
            logger.info("Construction rule triggered: %s = %s (%+.1f%%, ₹%.0f)", feat_key, feat_val, pct, impact_amount)

    # Process list of premium features/addons
    premium_feats = features.get("premium_features") or []
    if isinstance(premium_feats, str):
        # in case LLM returned a comma-separated string instead of a list
        premium_feats = [x.strip() for x in premium_feats.split(",") if x.strip()]
        
    for pf in premium_feats:
        pf_clean = str(pf).lower().strip()
        if pf_clean in PREMIUM_ADDONS_RULES:
            pct, label, reason = PREMIUM_ADDONS_RULES[pf_clean]
            impact_amount = round(base_price * pct / 100.0, 2)
            total_pct += pct
            adjustments_list.append({
                "condition": label,
                "feature": label,
                "impact": impact_amount,
                "amount": impact_amount,
                "reason": reason
            })
            logger.info("Premium addon triggered: %s (%+.1f%%, ₹%.0f)", label, pct, impact_amount)

    total_adjustment = round(base_price * total_pct / 100.0, 2)
    return total_adjustment, adjustments_list
