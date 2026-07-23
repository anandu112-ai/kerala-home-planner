import logging

logger = logging.getLogger("kerala_home_planner.services.price_adjustment")

def calculate_adjustments(base_price: float, features: dict) -> dict:
    """
    Computes separate price adjustments based on extracted site features.
    
    Adjustments:
    - No vehicle access: -5%
    - Poor road: -3%
    - Hilly area: -2%
    - Beautiful scenic view: +5%
    - Good water availability: +2%
    - Flood risk: -8%
    
    Returns:
      dict with:
        "base_prediction": float
        "site_adjustment_amount": float
        "site_adjustment_percentage": float
        "final_prediction": float
        "detected_conditions": list of dict
    """
    adjustment_pct = 0.0
    detected_conditions = []
    
    # 1. No vehicle access: -5% (vehicle_access == "none")
    if features.get("vehicle_access") == "none":
        pct = -5.0
        impact = base_price * (pct / 100.0)
        adjustment_pct += pct
        detected_conditions.append({
            "condition": "No vehicle access",
            "impact": round(impact, 2),
            "reason": "Accessibility difficulty reduces market value"
        })
    
    # 2. Poor road: -3% (road_quality == "poor")
    if features.get("road_quality") == "poor":
        pct = -3.0
        impact = base_price * (pct / 100.0)
        adjustment_pct += pct
        detected_conditions.append({
            "condition": "Poor road",
            "impact": round(impact, 2),
            "reason": "Difficult road quality impacts approachability"
        })
        
    # 3. Hilly area: -2% (terrain_type == "hilly")
    if features.get("terrain_type") == "hilly":
        pct = -2.0
        impact = base_price * (pct / 100.0)
        adjustment_pct += pct
        detected_conditions.append({
            "condition": "Hilly area",
            "impact": round(impact, 2),
            "reason": "Sloped terrain increases building complexity and reduces valuation"
        })
        
    # 4. Beautiful scenic view: +5% (scenic_view == True)
    if features.get("scenic_view") is True:
        pct = 5.0
        impact = base_price * (pct / 100.0)
        adjustment_pct += pct
        detected_conditions.append({
            "condition": "Beautiful view",
            "impact": round(impact, 2),
            "reason": "Scenic advantage increases demand"
        })
        
    # 5. Good water availability: +2% (water_availability == "good")
    if features.get("water_availability") == "good":
        pct = 2.0
        impact = base_price * (pct / 100.0)
        adjustment_pct += pct
        detected_conditions.append({
            "condition": "Good water availability",
            "impact": round(impact, 2),
            "reason": "Reliable water supply adds premium value"
        })
        
    # 6. Flood risk: -8% (flood_risk == "yes")
    if features.get("flood_risk") == "yes":
        pct = -8.0
        impact = base_price * (pct / 100.0)
        adjustment_pct += pct
        detected_conditions.append({
            "condition": "Flood risk",
            "impact": round(impact, 2),
            "reason": "High vulnerability to seasonal floods drops property worth"
        })

    # Calculate final price
    adjustment_amount = base_price * (adjustment_pct / 100.0)
    final_price = base_price + adjustment_amount
    
    # Ensure final price is not negative
    final_price = max(0.0, final_price)

    return {
        "base_prediction": round(base_price, 2),
        "site_adjustment_amount": round(adjustment_amount, 2),
        "site_adjustment_percentage": round(adjustment_pct, 2),
        "final_prediction": round(final_price, 2),
        "detected_conditions": detected_conditions
    }
