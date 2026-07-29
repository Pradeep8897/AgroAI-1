from flask import Blueprint, request, jsonify
from backend.extensions import limiter
from backend.utils.jwt_handler import require_auth
import random
from datetime import datetime

assistant_bp = Blueprint('assistant', __name__)

BOT_RESPONSES = {
    "hello": [
        "Hello! I am AgroAI, your digital farming assistant. How can I help you today? You can ask me about crop recommendations, soil quality, market prices, or plant diseases.",
        "Namaste! Welcome to AgroAI. What crop-related advice or market price update can I assist you with today?"
    ],
    "soil": [
        "Soil fertility depends on Nitrogen (N), Phosphorus (P), Potassium (K), and organic carbon. A neutral pH of 6.0 to 7.0 is optimal for most food crops. What are your soil testing values? I can recommend a suitable crop or fertilizer recipe!",
        "Healthy soil should contain plenty of organic matter. If your soil is acidic (pH < 5.5), apply agricultural lime. If it is alkaline (pH > 7.5), incorporate organic compost or sulfur."
    ],
    "tomato": [
        "Tomatoes grow best in well-drained loamy soil with a pH of 6.0 - 6.8. They require steady watering and around 6-8 hours of sunlight. Watch out for 'Early Blight' or 'Late Blight' diseases which cause leaf spots.",
        "For a high yield of tomatoes, supply balanced NPK fertilizer initially, then shift to higher Potassium when fruit sets. Organic neem oil is excellent to keep fruit borers away."
    ],
    "blight": [
        "Blight is a common tomato/potato disease. If it's Early Blight (circular brown spots with rings), remove lower leaves and spray copper fungicide. If it's Late Blight (water-soaked dark spots with white fuzzy mold), isolate/remove the plants quickly as it spreads rapidly in humid weather."
    ],
    "price": [
        "You can check current market rates in our Market Intelligence section. Wheat is trading around ₹2,400/quintal, Basmati Rice is around ₹3,800/quintal, and Tomatoes fluctuate around ₹1,600-₹1,900/quintal. Prices depend heavily on Mandi arrival volumes.",
        "Market prices vary by state and Mandi. Our AI forecasts a bullish trend for Rice and Onion due to upcoming festive seasons. I recommend keeping an eye on local Mandi rates before selling."
    ],
    "mandi": [
        "Enter your Pincode in the Market Intelligence page to find the nearest government-approved Mandi along with contact details and distance!"
    ],
    "rent": [
        "Yes! You can rent tractors, harvesters, rotators, or seeders on an hourly basis in our Equipment Rental section. It's much cheaper than buying them."
    ],
    "organic": [
        "Organic farming uses compost manure, bone meal, bio-fertilizers, and botanical extracts for pest control. To control pests organically, spray a dilute solution of neem oil (5ml per liter of water with a drop of liquid soap) every two weeks."
    ]
}

DEFAULT_RESPONSES = [
    "That is an interesting question. In smart agriculture, we recommend testing soil NPK values and tracking humidity. Feel free to use the AgroAI Crop Recommendation or Disease Detection tools on the dashboard for automated analysis!",
    "I understand. For best results in your crop cycle, ensure proper irrigation timing and monitor leaf health. You can upload leaf photos directly to our Disease Detector to get immediate cure recipes.",
    "As an AI farming expert, I recommend using bio-fertilizers and organic mulching to preserve soil moisture. Let me know if you want me to calculate crop profitability margins!"
]

@assistant_bp.route('/api/assistant/chat', methods=['POST'])
@limiter.limit("30 per minute")
@require_auth(allowed_roles=['user', 'farmer', 'expert', 'admin'])
def chat():
    data = request.get_json() or {}
    message = data.get('message', '').lower().strip()
    
    if not message:
        return jsonify({"success": False, "message": "Message content is empty."}), 400

    # Pattern match key terms
    response_text = None
    for keyword, responses in BOT_RESPONSES.items():
        if keyword in message:
            response_text = random.choice(responses)
            break
            
    if not response_text:
        response_text = random.choice(DEFAULT_RESPONSES)

    return jsonify({
        "success": True,
        "reply": response_text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
