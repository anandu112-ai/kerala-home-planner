import sys
import os

# Adjust path to import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

def test_endpoints():
    client = TestClient(app)
    
    # Test Payload
    payload = {
        "district": "Thiruvananthapuram",
        "built_up_area_sqft": 2000.0,
        "plot_size_cents": 7.0,
        "bedrooms": 3,
        "bathrooms": 3,
        "floors": 2,
        "parking_spaces": 1,
        "balconies": 2,
        "kitchen_type": "Modular",
        "quality": "Standard",
        "roof_type": "RCC",
        "flooring": "Vitrified Tile",
        "budget": 5500000.0,
        "addons": ["Solar"],
        "site_description": "House in Kowdiar prime area. Normal vehicle access, scenic valley view, good road connection."
    }
    
    print("Testing /predict endpoint...")
    response = client.post("/predict", json=payload)
    
    if response.status_code != 200:
        print(f"Error calling /predict: {response.status_code}")
        print(response.text)
        sys.exit(1)
        
    res_data = response.json()
    print("Successfully received prediction response!")
    print(f"Base Predicted Cost: {res_data.get('predicted_cost')}")
    print(f"Final Predicted Price: {res_data.get('predicted_price')}")
    
    prediction_id = res_data.get("prediction_id")
    print(f"Prediction ID: {prediction_id}")
    
    similar_props = res_data.get("similar_properties", [])
    print(f"Found {len(similar_props)} similar properties:")
    for p in similar_props:
        print(f" - Location: {p['location']}, Area: {p['built_up_area_sqft']}, Price: {p['price']}, Similarity: {p['similarity']}%")
        
    market_analysis = res_data.get("market_analysis", {})
    print(f"Market Analysis: {market_analysis}")
    
    ai_explanation = res_data.get("ai_explanation")
    print(f"AI Explanation (truncated): {ai_explanation[:200]}...")
    
    # Verify similar properties logic worked
    assert len(similar_props) > 0, "No similar properties found"
    assert "average_price" in market_analysis, "market_analysis is missing average_price"
    assert prediction_id is not None, "prediction_id is missing"
    
    # Test PDF Report Generation Endpoint
    print(f"\nTesting /api/v1/report/{prediction_id} endpoint...")
    report_response = client.get(f"/api/v1/report/{prediction_id}")
    
    if report_response.status_code != 200:
        print(f"Error calling /api/v1/report: {report_response.status_code}")
        print(report_response.text)
        sys.exit(1)
        
    pdf_bytes = report_response.content
    print(f"Successfully generated PDF report! Size: {len(pdf_bytes)} bytes.")
    
    assert len(pdf_bytes) > 0, "PDF size is 0 bytes"
    assert report_response.headers.get("content-type") == "application/pdf", "Content-Type is not application/pdf"
    
    print("\nAll backend integration tests passed successfully!")

if __name__ == "__main__":
    test_endpoints()
