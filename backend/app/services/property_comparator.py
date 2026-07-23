import logging

logger = logging.getLogger("kerala_home_planner.services.property_comparator")

try:
    from app.services.properties_db import PROPERTIES_DATASET
except ImportError:
    from services.properties_db import PROPERTIES_DATASET

def quality_score(q: str) -> float:
    scores = {"basic": 1.0, "standard": 2.0, "premium": 3.0, "luxury": 4.0}
    return scores.get(str(q).lower().strip(), 2.0)

def flooring_score(f: str) -> float:
    scores = {"cement": 1.0, "vitrified tile": 2.0, "granite": 3.0, "marble": 4.0}
    return scores.get(str(f).lower().strip(), 2.0)

def generate_ai_explanation(ip: dict, market_analysis: dict, final_price: float, adjustments: list) -> str:
    avg_price = market_analysis.get("average_price", 0)
    position = market_analysis.get("position", "at market value")
    price_diff = market_analysis.get("price_difference", 0)
    district = ip.get("district", "Ernakulam")
    
    try:
        from app.services.pdf_report_generator import format_inr
    except ImportError:
        try:
            from services.pdf_report_generator import format_inr
        except ImportError:
            def format_inr(v):
                return f"₹{v:,.0f}"
                
    price_str = format_inr(final_price)
    avg_str = format_inr(avg_price)
    diff_str = format_inr(abs(price_diff))
    
    if "below" in position:
        p1 = f"The estimated property value of {price_str} is positioned {position}, standing approximately {diff_str} below the market average of {avg_str} for comparable homes in {district}. This suggests that the current design and specifications represent a cost-effective opportunity compared to active local developer benchmarks."
    elif "above" in position:
        p1 = f"The estimated property value of {price_str} is positioned {position}, standing approximately {diff_str} above the regional market average of {avg_str} for {district}. This premium pricing is primarily driven by your choice of superior materials, advanced finishes (such as {ip.get('flooring', 'Vitrified Tile')}), or custom architectural features."
    else:
        p1 = f"The estimated property value of {price_str} is well-aligned with the regional market average of {avg_str} for comparable homes in {district}. This indicates the project cost is optimized with standard local construction guidelines and material pricing."
        
    site_adjustments = []
    for adj in adjustments:
        cond_lower = adj.get("condition", "").lower()
        is_const = any(x in cond_lower for x in [
            "material", "flooring", "wood", "teak", "kitchen", "sanitary", 
            "electrical", "automation", "solar", "pool", "landscaping", "grade"
        ])
        if not is_const:
            site_adjustments.append(adj)
            
    if site_adjustments:
        cond_names = [adj.get("condition") for adj in site_adjustments]
        cond_str = ", ".join(cond_names)
        p2 = f"Crucially, the site assessment highlighted location and accessibility adjustments: {cond_str}. In particular, addressing any access constraints (such as road widening or leveling) could help reduce material transport overheads and immediately unlock extra valuation potential."
    else:
        p2 = "The property location features standard accessibility, and no major terrain or flood risks were flagged. This provides a stable construction canvas and minimizes foundation engineering cost overheads."
        
    p3 = "The overall property represents a solid layout. To optimize future resale yield, focus on durable exterior weatherproofing (critical for Kerala's monsoons) and explore green features like grid-tied solar panels which offer both long-term energy savings and a green value premium in the market."
    
    return f"{p1}\n\n{p2}\n\n{p3}"

def find_similar_properties(ip: dict, base_predicted_price: float, adjustments: list = None) -> dict:
    """
    Finds properties in the dataset similar to the input property.
    Uses a weighted multi-attribute similarity metric (similar to a custom KNN / Cosine Similarity).
    
    Parameters:
    - ip: input property dictionary (with keys district, built_up_area_sqft, bedrooms, etc.)
    - base_predicted_price: ML base predicted price or final prediction
    - adjustments: list of construction/site adjustments
    
    Returns:
    - dict: {
        "similar_properties": List[dict],
        "market_analysis": dict,
        "ai_explanation": str
      }
    """
    ip_area = float(ip.get("built_up_area_sqft", 1500))
    ip_plot = float(ip.get("plot_size_cents", 7.0))
    ip_beds = int(ip.get("bedrooms", 3))
    ip_baths = int(ip.get("bathrooms", 3))
    ip_district = str(ip.get("district", "Ernakulam")).strip()
    ip_quality = str(ip.get("quality", "Standard")).strip()
    ip_flooring = str(ip.get("flooring", "Vitrified Tile")).strip()
    ip_kitchen = str(ip.get("kitchen_type", "Modular")).strip()

    scored_properties = []

    for p in PROPERTIES_DATASET:
        # 1. District match
        dist_match = 1.0 if p["district"].lower() == ip_district.lower() else 0.1
        
        # 2. Built up area similarity (exponential decay for difference)
        area_diff = abs(p["built_up_area_sqft"] - ip_area)
        area_sim = 1.0 - (area_diff / max(p["built_up_area_sqft"], ip_area, 1))

        # 3. Plot size similarity
        plot_diff = abs(p["plot_size_cents"] - ip_plot)
        plot_sim = 1.0 - (plot_diff / max(p["plot_size_cents"], ip_plot, 1))

        # 4. Bedrooms similarity
        bed_diff = abs(p["bedrooms"] - ip_beds)
        bed_sim = 1.0 - (bed_diff / max(p["bedrooms"], ip_beds, 1))

        # 5. Bathrooms similarity
        bath_diff = abs(p["bathrooms"] - ip_baths)
        bath_sim = 1.0 - (bath_diff / max(p["bathrooms"], ip_baths, 1))

        # 6. Quality similarity
        qual_sim = 1.0 - (abs(quality_score(p["quality"]) - quality_score(ip_quality)) / 3.0)

        # 7. Flooring similarity
        floor_sim = 1.0 - (abs(flooring_score(p["flooring"]) - flooring_score(ip_flooring)) / 3.0)

        # 8. Kitchen similarity
        kitchen_sim = 1.0 if p["kitchen_type"].lower() == ip_kitchen.lower() else 0.6

        # Calculate weighted average similarity including construction details
        similarity = (
            dist_match * 0.25 +
            area_sim * 0.25 +
            bed_sim * 0.15 +
            qual_sim * 0.15 +
            kitchen_sim * 0.10 +
            floor_sim * 0.05 +
            plot_sim * 0.05
        )

        similarity_pct = round(max(0.0, min(1.0, similarity)) * 100, 1)

        # Append data
        scored_properties.append({
            "district": p["district"],
            "location": p["location"],
            "built_up_area_sqft": p["built_up_area_sqft"],
            "bedrooms": p["bedrooms"],
            "quality": p["quality"],
            "price": p["price"],
            "similarity": similarity_pct
        })

    # Sort properties by similarity score in descending order
    scored_properties.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Get top 3 similar properties
    similar_list = scored_properties[:3]

    # Calculate statistics based on the top matches (or fallback on dataset if needed)
    prices = [p["price"] for p in similar_list]
    if not prices:
        # Fallback if no properties
        prices = [base_predicted_price]
        similar_list = [{
            "location": "Local Area",
            "district": ip_district,
            "built_up_area_sqft": ip_area,
            "bedrooms": ip_beds,
            "quality": ip_quality,
            "price": base_predicted_price,
            "similarity": 100.0
        }]

    avg_price = round(sum(prices) / len(prices), 2)
    lowest_price = round(min(prices), 2)
    highest_price = round(max(prices), 2)
    price_diff = round(base_predicted_price - avg_price, 2)

    # Position text
    pct_diff = (price_diff / avg_price) if avg_price > 0 else 0
    if pct_diff < -0.10:
        position = "significantly below market"
    elif pct_diff < -0.02:
        position = "slightly below market"
    elif pct_diff > 0.10:
        position = "significantly above market"
    elif pct_diff > 0.02:
        position = "slightly above market"
    else:
        position = "at market value"

    market_analysis = {
        "average_price": avg_price,
        "lowest_price": lowest_price,
        "highest_price": highest_price,
        "price_difference": price_diff,
        "position": position
    }

    logger.info("Similarity search completed. Top similarity: %.1f%%, Market avg: ₹%.2f", 
                similar_list[0]["similarity"] if similar_list else 0, avg_price)

    ai_explanation = generate_ai_explanation(ip, market_analysis, base_predicted_price, adjustments or [])

    return {
        "similar_properties": similar_list,
        "market_analysis": market_analysis,
        "ai_explanation": ai_explanation
    }

