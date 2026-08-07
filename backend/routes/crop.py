from flask import Blueprint, request, jsonify
from models.crop import CropModel
import math
import os
import pickle
from datetime import datetime, timedelta

crop_bp = Blueprint('crop', __name__)

# Standard crop profile database (centroids of soil/climate requirements)
CROP_PROFILES = [
    {"name": "Rice", "N": 100, "P": 50, "K": 50, "ph": 6.5, "temp": 28.0, "humidity": 82.0, "rainfall": 220.0},
    {"name": "Maize (Corn)", "N": 90, "P": 45, "K": 40, "ph": 6.2, "temp": 25.0, "humidity": 68.0, "rainfall": 90.0},
    {"name": "Cotton", "N": 110, "P": 55, "K": 50, "ph": 6.5, "temp": 30.0, "humidity": 75.0, "rainfall": 80.0},
    {"name": "Wheat", "N": 80, "P": 40, "K": 40, "ph": 6.8, "temp": 18.0, "humidity": 55.0, "rainfall": 60.0},
    {"name": "Chickpea (Chana)", "N": 30, "P": 70, "K": 35, "ph": 7.0, "temp": 22.0, "humidity": 45.0, "rainfall": 40.0},
    {"name": "Kidney Beans (Rajma)", "N": 35, "P": 65, "K": 35, "ph": 6.0, "temp": 20.0, "humidity": 50.0, "rainfall": 75.0},
    {"name": "Coffee", "N": 100, "P": 30, "K": 90, "ph": 5.5, "temp": 23.0, "humidity": 75.0, "rainfall": 180.0},
    {"name": "Grapes", "N": 30, "P": 30, "K": 80, "ph": 6.0, "temp": 24.0, "humidity": 60.0, "rainfall": 65.0},
    {"name": "Mango", "N": 40, "P": 25, "K": 40, "ph": 6.3, "temp": 32.0, "humidity": 50.0, "rainfall": 120.0},
    {"name": "Banana", "N": 100, "P": 75, "K": 120, "ph": 6.5, "temp": 27.0, "humidity": 80.0, "rainfall": 160.0}
]

models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai-models")
crop_model_path = os.path.join(models_dir, "crop_model.pkl")
crop_model = None

try:
    if os.path.exists(crop_model_path):
        with open(crop_model_path, "rb") as f:
            crop_model = pickle.load(f)
        print("Scikit-Learn crop_model.pkl loaded successfully!")
except Exception as e:
    print(f"Error loading crop model: {e}")

def calculate_suitability(inputs, profile):
    # Normalized Euclidean distance calculation
    weights = {
        "N": 0.01,
        "P": 0.01,
        "K": 0.01,
        "ph": 0.5,
        "temp": 0.05,
        "humidity": 0.02,
        "rainfall": 0.005
    }
    
    total_dist = 0
    for key in weights:
        dist = (inputs[key] - profile[key]) * weights[key]
        total_dist += dist ** 2
        
    distance = math.sqrt(total_dist)
    similarity = max(0, 100 - (distance * 15))
    return round(similarity, 1)

@crop_bp.route('/api/crop/recommend', methods=['POST'])
def recommend_crop():
    data = request.get_json() or {}
    try:
        user_id = data.get('user_id')
        N = float(data.get('N', 0))
        P = float(data.get('P', 0))
        K = float(data.get('K', 0))
        ph = float(data.get('ph', 6.0))
        temp = float(data.get('temp', 25.0))
        humidity = float(data.get('humidity', 60.0))
        rainfall = float(data.get('rainfall', 100.0))
    except ValueError:
        return jsonify({"success": False, "message": "Parameters must be numeric."}), 400

    inputs = {"N": N, "P": P, "K": K, "ph": ph, "temp": temp, "humidity": humidity, "rainfall": rainfall}
    
    if crop_model:
        # Real ML Inference using the loaded model
        features = [N, P, K, ph, temp, humidity, rainfall]
        prediction_idx = int(crop_model.predict([features])[0])
        top_crop = crop_model.crop_labels_.get(prediction_idx, "Rice")
        
        # Calculate dynamic probabilities
        probabilities = crop_model.predict_proba([features])[0]
        recs = []
        for idx, prob in enumerate(probabilities):
            crop_name = crop_model.crop_labels_.get(idx, "Unknown")
            # If the model has 0 probability, we can assign a tiny baseline similarity
            recs.append({
                "crop": crop_name,
                "score": max(5.0, round(prob * 100, 1))
            })
        recs.sort(key=lambda x: x["score"], reverse=True)
        top_crop = recs[0]["crop"]
        top_score = recs[0]["score"]
        alternatives = recs[1:4]
    else:
        # Fallback heuristic logic
        recommendations = []
        for profile in CROP_PROFILES:
            score = calculate_suitability(inputs, profile)
            recommendations.append({
                "crop": profile["name"],
                "score": score,
                "profile": profile
            })
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        top_crop = recommendations[0]["crop"]
        top_score = recommendations[0]["score"]
        alternatives = recommendations[1:4]
    
    # Save search to database
    CropModel.save_recommendation(user_id, top_crop, N, P, K, ph, temp, humidity, rainfall, f"{top_crop} ({top_score}%)")

    return jsonify({
        "success": True,
        "input_summary": inputs,
        "top_recommendation": top_crop,
        "score": top_score,
        "alternatives": alternatives
    })

@crop_bp.route('/api/crop/fertilizer', methods=['POST'])
def recommend_fertilizer():
    data = request.get_json() or {}
    target_crop = data.get('crop', 'Rice')
    try:
        N = float(data.get('N', 0))
        P = float(data.get('P', 0))
        K = float(data.get('K', 0))
    except ValueError:
        return jsonify({"success": False, "message": "NPK values must be numeric."}), 400

    # Get target crop requirements
    profile = next((p for p in CROP_PROFILES if p["name"].lower() == target_crop.lower()), None)
    if not profile:
        profile = CROP_PROFILES[0] # Default to rice

    n_diff = profile["N"] - N
    p_diff = profile["P"] - P
    k_diff = profile["K"] - K

    recommendations = []
    
    if n_diff > 15:
        recommendations.append({
            "nutrient": "Nitrogen (N)",
            "status": f"Deficient by {round(n_diff)} mg/kg",
            "treatment": "Apply Nitrogen fertilizers. Recommended dosage: Urea (46% N) at 80-100 kg/acre, or Ammonium Nitrate.",
            "organic_alternative": "Incorporate well-rotted farmyard manure (FYM), compost, or plant nitrogen-fixing cover crops like alfalfa/clover."
        })
    elif n_diff < -20:
        recommendations.append({
            "nutrient": "Nitrogen (N)",
            "status": f"Excessive by {round(abs(n_diff))} mg/kg",
            "treatment": "Avoid nitrogenous fertilizers. Flush soil with heavy watering if drainage is good, or plant heavy feeder crops.",
            "organic_alternative": "Incorporate carbon-rich materials like wood chips, straw, or sawdust to temporarily tie up excess soil nitrogen."
        })

    if p_diff > 10:
        recommendations.append({
            "nutrient": "Phosphorus (P)",
            "status": f"Deficient by {round(p_diff)} mg/kg",
            "treatment": "Apply phosphate fertilizers. Recommended: Single Super Phosphate (SSP) at 120 kg/acre, or Diammonium Phosphate (DAP).",
            "organic_alternative": "Apply rock phosphate or bone meal directly into the root zone before transplanting."
        })

    if k_diff > 10:
        recommendations.append({
            "nutrient": "Potassium (K)",
            "status": f"Deficient by {round(k_diff)} mg/kg",
            "treatment": "Apply potash fertilizers. Recommended: Muriate of Potash (MOP) at 50 kg/acre.",
            "organic_alternative": "Incorporate wood ash (sparingly, as it increases pH), greensand, or kelp meal into the soil."
        })

    if not recommendations:
        recommendations.append({
            "nutrient": "Balanced Soil",
            "status": "Soil NPK levels match target crop profile.",
            "treatment": "Maintain current nutrient balance with light compost mulch.",
            "organic_alternative": "Add light compost tea during vegetative growth."
        })

    return jsonify({
        "success": True,
        "crop": target_crop,
        "ideal_profile": {"N": profile["N"], "P": profile["P"], "K": profile["K"]},
        "soil_profile": {"N": N, "P": P, "K": K},
        "recommendations": recommendations
    })

@crop_bp.route('/api/crop/calendar', methods=['POST'])
def get_calendar():
    data = request.get_json() or {}
    crop_name = data.get('crop', 'Rice')
    planting_date_str = data.get('planting_date', datetime.now().strftime("%Y-%m-%d"))

    try:
        planting_date = datetime.strptime(planting_date_str, "%Y-%m-%d")
    except ValueError:
        planting_date = datetime.now()

    # Standard cycle structures
    calendars = {
        "rice": [
            {"phase": "Land Preparation", "duration_days": 10, "activity": "Plough fields, establish levees, and apply organic compost."},
            {"phase": "Sowing & Nursery", "duration_days": 25, "activity": "Sow pre-germinated seeds in nurseries and maintain shallow water level."},
            {"phase": "Transplanting", "duration_days": 5, "activity": "Transplant 25-day old seedlings into main puddled field (2-3 cm standing water)."},
            {"phase": "Tillering & Vegetative", "duration_days": 45, "activity": "Apply first top-dressing of Urea. Keep fields clear of weeds."},
            {"phase": "Panicle Initiation", "duration_days": 20, "activity": "Maintain water level at 5 cm. Monitor for stem borers and blast disease."},
            {"phase": "Ripening & Harvesting", "duration_days": 30, "activity": "Drain water 10 days before harvest. Cut plants and dry grains in sun."}
        ],
        "wheat": [
            {"phase": "Sowing", "duration_days": 7, "activity": "Prepare fine seedbed, sow seeds at 4-5 cm depth with seed-drill."},
            {"phase": "Crown Root Initiation", "duration_days": 21, "activity": "First irrigation cycle (critical phase). Apply first dosage of Urea."},
            {"phase": "Tillering & Jointing", "duration_days": 35, "activity": "Second irrigation. Spray weedicides if necessary. Keep soil moist."},
            {"phase": "Flowering & Milk Stage", "duration_days": 35, "activity": "Third and fourth irrigation. Monitor for wheat rust infections."},
            {"phase": "Dough & Maturity", "duration_days": 25, "activity": "Grains turn hard and golden. Stop irrigation. Harvest when moisture is < 14%."}
        ],
        "default": [
            {"phase": "Seed Sowing", "duration_days": 7, "activity": "Prepare soil mix, plant seeds, water gently and ensure light."},
            {"phase": "Vegetative Growth", "duration_days": 40, "activity": "Apply nitrogenous compost. Prune off side shoots to encourage vertical growth."},
            {"phase": "Flowering Stage", "duration_days": 25, "activity": "Increase phosphorus intake. Ensure adequate pollination and moisture."},
            {"phase": "Harvesting", "duration_days": 20, "activity": "Monitor fruit/grain ripening. Harvest at optimal mature state."}
        ]
    }

    key = crop_name.lower().split(' ')[0]
    stages = calendars.get(key, calendars["default"])
    
    timeline = []
    current_date = planting_date
    for idx, stage in enumerate(stages):
        end_date = current_date + timedelta(days=stage["duration_days"])
        timeline.append({
            "stage_number": idx + 1,
            "phase": stage["phase"],
            "start_date": current_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "duration": f"{stage['duration_days']} days",
            "activity": stage["activity"]
        })
        current_date = end_date

    return jsonify({
        "success": True,
        "crop": crop_name,
        "planting_date": planting_date.strftime("%Y-%m-%d"),
        "timeline": timeline
    })

@crop_bp.route('/api/crop/history', methods=['GET'])
def get_crop_history():
    user_id = request.args.get('user_id')
    history = CropModel.get_history_by_user(user_id)
    return jsonify({
        "success": True,
        "history": history
    })
