from typing import List

# -----------------------------
# Stage-wise Cost Distribution
# -----------------------------

STAGE_PERCENTAGES = {
    "Foundation": 12,
    "Structure": 30,
    "Roofing": 10,
    "Electrical": 8,
    "Plumbing": 8,
    "Flooring": 10,
    "Painting": 7,
    "Finishing": 15,
}

# -----------------------------
# Optional Add-ons
# -----------------------------

ADDON_COSTS = {
    "Compound Wall": 250000,
    "Gate": 80000,
    "Car Porch": 150000,
    "Borewell": 120000,
    "Septic Tank": 100000,
    "Solar Panels": 300000,
    "False Ceiling": 180000,
    "Interior Work": 500000,
    "Landscaping": 200000,
    "Smart Home": 250000,
    "CCTV": 60000,
}


# -----------------------------
# Cost Range
# -----------------------------

def calculate_cost_range(cost: float):
    return {
        "min": round(cost * 0.97, 2),
        "max": round(cost * 1.03, 2)
    }


# -----------------------------
# Cost Per Sq.ft.
# -----------------------------

def cost_per_sqft(cost: float, area: float):
    return round(cost / area, 2)


# -----------------------------
# House Category
# -----------------------------

def house_category(cost: float):

    if cost < 2500000:
        return "Budget House"

    elif cost < 5000000:
        return "Standard House"

    elif cost < 8000000:
        return "Premium House"

    return "Luxury House"


# -----------------------------
# Construction Duration
# -----------------------------

def construction_time(area: float, floors: int):

    if area < 1200:
        months = "5–6 Months"

    elif area < 1800:
        months = "6–8 Months"

    elif area < 2500:
        months = "8–10 Months"

    else:
        months = "10–14 Months"

    if floors > 1:
        months += " (Approx.)"

    return months


# -----------------------------
# Budget Analysis
# -----------------------------

def budget_analysis(cost: float, budget: float):

    utilization = round((cost / budget) * 100, 2)

    if budget > cost:

        return {
            "status": "Within Budget",
            "surplus": round(budget - cost, 2),
            "deficit": 0,
            "utilization": utilization
        }

    elif abs(cost - budget) <= 200000:

        return {
            "status": "Budget Tight",
            "surplus": 0,
            "deficit": round(cost - budget, 2),
            "utilization": utilization
        }

    return {
        "status": "Budget Short",
        "surplus": 0,
        "deficit": round(cost - budget, 2),
        "utilization": utilization
    }


# -----------------------------
# Stage Breakdown
# -----------------------------

def stage_breakdown(cost: float):

    stages = []

    for stage, percent in STAGE_PERCENTAGES.items():

        stages.append({
            "stage": stage,
            "percentage": percent,
            "cost": round(cost * percent / 100, 2)
        })

    return stages


# -----------------------------
# Optional Add-ons
# -----------------------------

ADDON_MAPPING = {
    "compound": "Compound Wall",
    "gate": "Gate",
    "carporch": "Car Porch",
    "borewell": "Borewell",
    "septic": "Septic Tank",
    "solar": "Solar Panels",
    "ceiling": "False Ceiling",
    "interior": "Interior Work",
    "landscape": "Landscaping",
    "smart": "Smart Home",
    "cctv": "CCTV",
}

def addon_summary(selected_addons: List[str]):

    addon_list = []

    total = 0

    for addon in selected_addons:

        mapped_name = ADDON_MAPPING.get(addon, addon)
        price = ADDON_COSTS.get(mapped_name, 0)

        addon_list.append({
            "name": mapped_name,
            "cost": price
        })

        total += price

    return {
        "selected": addon_list,
        "total_cost": total
    }


# -----------------------------
# Construction Health Score
# -----------------------------

def health_score(cost: float, budget: float, floors: int):

    score = 70

    if budget >= cost:
        score += 15

    if floors == 1:
        score += 5

    if budget > cost * 1.1:
        score += 10

    return min(score, 100)


# -----------------------------
# Smart Recommendations
# -----------------------------

def recommendations(data: dict, predicted_cost: float):

    recs = []

    budget = data["budget"]

    if budget >= predicted_cost:

        recs.append({
            "type": "success",
            "title": "Budget is Sufficient",
            "description": "Your available budget can comfortably cover this project.",
            "priority": "Low",
            "estimated_cost_impact": "No additional cost"
        })

        recs.append({
            "type": "upgrade",
            "title": "Consider Solar Panels",
            "description": "Long-term electricity savings and eco-friendly construction.",
            "priority": "Medium",
            "estimated_cost_impact": "₹3,00,000"
        })

    else:

        recs.append({
            "type": "warning",
            "title": "Budget Short",
            "description": "Increase budget or optimize the design.",
            "priority": "High",
            "estimated_cost_impact": "Depends on modifications"
        })

        if data["built_up_area_sqft"] > 1800:

            recs.append({
                "type": "optimization",
                "title": "Reduce Built-up Area",
                "description": "Reducing 100–200 sq.ft. can significantly lower cost.",
                "priority": "High",
                "estimated_cost_impact": "Save ₹2–5 Lakhs"
            })

        if data["quality"] == "Premium":

            recs.append({
                "type": "optimization",
                "title": "Choose Standard Quality",
                "description": "Standard quality offers good durability at a lower cost.",
                "priority": "Medium",
                "estimated_cost_impact": "Save ₹3–7 Lakhs"
            })

        if data["flooring"] == "Premium":

            recs.append({
                "type": "optimization",
                "title": "Use Standard Flooring",
                "description": "Standard vitrified tiles reduce finishing costs.",
                "priority": "Medium",
                "estimated_cost_impact": "Save ₹80K–1.5L"
            })

    return recs