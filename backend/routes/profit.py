from flask import Blueprint, request, jsonify
from backend.extensions import limiter
from backend.utils.jwt_handler import require_auth

profit_bp = Blueprint('profit', __name__)

@profit_bp.route('/api/profit/optimize', methods=['POST'])
@limiter.limit("20 per minute")
@require_auth(allowed_roles=['user', 'farmer', 'expert', 'admin'])
def optimize_profit():
    data = request.get_json() or {}
    
    # Cost structures
    seed_cost = float(data.get('seed_cost', 0))
    fertilizer_cost = float(data.get('fertilizer_cost', 0))
    pesticide_cost = float(data.get('pesticide_cost', 0))
    labor_cost = float(data.get('labor_cost', 0))
    rentals_cost = float(data.get('rentals_cost', 0))
    irrigation_cost = float(data.get('irrigation_cost', 0))
    other_cost = float(data.get('other_cost', 0))
    
    # Revenue projections
    expected_yield = float(data.get('expected_yield', 0)) # in quintals (100kg)
    selling_price = float(data.get('selling_price', 0)) # price per quintal
    
    total_cost = (seed_cost + fertilizer_cost + pesticide_cost + 
                  labor_cost + rentals_cost + irrigation_cost + other_cost)
                  
    expected_revenue = expected_yield * selling_price
    net_profit = expected_revenue - total_cost
    
    roi = 0.0
    if total_cost > 0:
        roi = round((net_profit / total_cost) * 100, 2)

    # Automated advice triggers based on margin and budget weights
    suggestions = []
    
    # Analyze labor cost ratio
    if total_cost > 0 and (labor_cost / total_cost) > 0.4:
        suggestions.append({
            "category": "Labor Cost",
            "message": "Labor costs account for over 40% of your expenses. Consider machine rentals (tractor/seeder) to automate planting and sowing to cut manual labor hours."
        })
        
    # Analyze fertilizer cost vs yield
    if total_cost > 0 and (fertilizer_cost / total_cost) > 0.3:
        suggestions.append({
            "category": "Fertilizer Expense",
            "message": "Fertilizers are high. Perform a soil test and switch to targeted micro-dose fertilizer applications or organic compost manures to lower expense by 15-20%."
        })

    # Analyze water/irrigation
    if total_cost > 0 and (irrigation_cost / total_cost) > 0.15:
        suggestions.append({
            "category": "Irrigation Efficiency",
            "message": "Irrigation cost is high. Consider setting up a subsidised micro-drip irrigation system to reduce water wastage and pumping electricity costs."
        })

    # Generic revenue improvement
    if roi < 15:
        suggestions.append({
            "category": "Revenue Boost",
            "message": "Low return on investment predicted. Sell products through AgroAI Marketplace directly to consumers or local stores to obtain 10-15% higher prices than traditional intermediaries."
        })
    else:
        suggestions.append({
            "category": "Pest & Disease Shielding",
            "message": "Healthy crop ROI estimated. Safeguard this crop by running weekly leaf image tests in the AgroAI Disease Detector to prevent late blight or rust epidemics."
        })

    return jsonify({
        "success": True,
        "summary": {
            "total_cost": round(total_cost, 2),
            "expected_revenue": round(expected_revenue, 2),
            "net_profit": round(net_profit, 2),
            "roi_percent": roi
        },
        "breakdown": {
            "seeds": seed_cost,
            "fertilizers": fertilizer_cost,
            "pesticides": pesticide_cost,
            "labor": labor_cost,
            "rentals": rentals_cost,
            "irrigation": irrigation_cost,
            "other": other_cost
        },
        "suggestions": suggestions
    })
