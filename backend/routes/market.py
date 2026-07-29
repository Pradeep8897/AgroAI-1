from flask import Blueprint, request, jsonify
from backend.models.market import MarketModel
from backend.utils.jwt_handler import require_auth
import os
import joblib
import random
from datetime import datetime, timedelta

market_bp = Blueprint('market', __name__)

models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai-models")
market_model_path = os.path.join(models_dir, "market_model.pkl")
market_model = None

try:
    if os.path.exists(market_model_path):
        market_model = joblib.load(market_model_path)
        print("Scikit-Learn market_model.pkl loaded successfully!")
except Exception as e:
    print(f"Error loading market model: {e}")

MANDI_REGISTRY = {
    "110001": [
        {"name": "Azadpur Mandi", "distance": "3.5 km", "address": "Azadpur, New Delhi, Delhi 110033", "phone": "+91 11 2767 1234"},
        {"name": "Okhla Sabzi Mandi", "distance": "12.0 km", "address": "Okhla Phase II, New Delhi, Delhi 110020", "phone": "+91 11 2638 5678"}
    ],
    "400001": [
        {"name": "Vashi APMC Mandi", "distance": "5.2 km", "address": "Sector 19, Vashi, Navi Mumbai, Maharashtra 400703", "phone": "+91 22 2765 4321"},
        {"name": "Dadar Flower & Vegetable Market", "distance": "8.1 km", "address": "Dadar West, Mumbai, Maharashtra 400028", "phone": "+91 22 2430 9876"}
    ],
    "452001": [
        {"name": "Choithram Mandi", "distance": "4.0 km", "address": "Dhar Road, Indore, Madhya Pradesh 452002", "phone": "+91 731 234 5678"},
        {"name": "Laxmibai Nagar Mandi", "distance": "9.5 km", "address": "Fort Road, Indore, Madhya Pradesh 452006", "phone": "+91 731 245 8765"}
    ],
    "132001": [
        {"name": "Karnal Grain Market", "distance": "2.1 km", "address": "GT Road, Karnal, Haryana 132001", "phone": "+91 184 225 1209"}
    ]
}

DEFAULT_MANDIS = [
    {"name": "Regional Agricultural Mandi", "distance": "12.4 km", "address": "District Main Highway Road, Sector 4", "phone": "+91 99999 88888"},
    {"name": "Central Grain Yard Mandi", "distance": "18.1 km", "address": "Railway Station Road, Block B", "phone": "+91 99999 77777"}
]

@market_bp.route('/api/market/prices', methods=['GET'])
def get_prices():
    crop = request.args.get('crop', '')
    if crop:
        prices = MarketModel.get_prices_by_crop(crop)
    else:
        prices = MarketModel.get_all_prices()
    return jsonify({
        "success": True,
        "prices": prices
    })

@market_bp.route('/api/market/predict', methods=['POST'])
@require_auth(allowed_roles=['user', 'farmer', 'expert', 'admin'])
def predict_price():
    data = request.get_json() or {}
    crop = data.get('crop', 'Tomato')
    months_ahead = int(data.get('months', 3))

    crop_ids = {"Tomato": 0, "Potato": 1, "Rice": 2, "Wheat": 3, "Corn": 4}
    crop_bases = {"Tomato": 1800.0, "Potato": 1200.0, "Rice": 3800.0, "Wheat": 2400.0, "Corn": 2100.0}
    
    crop_id = crop_ids.get(crop, 0)
    base_price = crop_bases.get(crop, 2000.0)
    
    # Generate historical months (simulate using the base price and minor noise)
    history = []
    current_date = datetime.now() - timedelta(days=150)
    for i in range(5):
        hist_date = current_date + timedelta(days=i*30)
        hist_val = base_price + random.uniform(-100, 100)
        history.append({
            "month": hist_date.strftime("%B %Y"),
            "price": round(hist_val, 2),
            "demand": random.choice(["Medium", "High", "Low"])
        })

    # Generate predictions using the regression model
    predictions = []
    projected_date = datetime.now()
    
    for i in range(1, months_ahead + 1):
        projected_date = projected_date + timedelta(days=30)
        
        if market_model:
            # Query Scikit-Learn model: shape (1, 2)
            pred_val = float(market_model.predict([[crop_id, i]])[0])
            # Add minor random noise for local variation
            pred_val += random.uniform(-20, 20)
        else:
            # Fallback heuristic
            trend = i * 25.0 if crop in ["Tomato", "Rice"] else i * -10.0
            pred_val = base_price + trend
            
        pred_val = max(500.0, round(pred_val, 2))
        demand_status = "High" if pred_val > base_price * 1.05 else ("Low" if pred_val < base_price * 0.95 else "Medium")
        
        predictions.append({
            "month": projected_date.strftime("%B %Y"),
            "price": pred_val,
            "demand": demand_status,
            "confidence": round(95.0 - (i * 2.5), 1)
        })

    current_val = history[-1]["price"]
    return jsonify({
        "success": True,
        "crop": crop,
        "historical_data": history,
        "predictions": predictions,
        "market_sentiment": "Bullish" if predictions[-1]["price"] > current_val else "Bearish"
    })

@market_bp.route('/api/market/mandis', methods=['GET'])
def get_mandis():
    pincode = request.args.get('pincode', '')
    
    # Retrieve local hubs from dictionary or fallback to default lists
    mandis = MANDI_REGISTRY.get(pincode, DEFAULT_MANDIS)
    
    return jsonify({
        "success": True,
        "pincode": pincode,
        "mandis": mandis
    })
