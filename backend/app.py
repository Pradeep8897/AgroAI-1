import logging
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, jsonify, send_from_directory, current_app
from flask_cors import CORS
from sqlalchemy import or_

from extensions import db
from database import init_database
from models.orm_models import Booking, Equipment, Listing, Order, Product

# Import Blueprints
from routes.auth import auth_bp
from routes.crop import crop_bp
from routes.disease import disease_bp
from routes.market import market_bp
from routes.profit import profit_bp
from routes.assistant import assistant_bp
from routes.admin import admin_bp
from routes.notification import notification_bp

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# Helper function to parse UUID safely
def parse_uuid(val):
    if not val:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError, TypeError):
        return None

init_database(app)
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        app.logger.warning(f"Startup create_all skipped or deferred: {e}")

@app.route("/")
def home():
    return {
        "status": "success",
        "message": "AgroAI Backend Running"
    }

# Enable CORS for frontend running on localhost:5173 or others
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Ensure upload directory exists (Use /tmp on Vercel)
if os.environ.get("VERCEL") == "1":
    UPLOAD_FOLDER = "/tmp/uploads"
else:
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(crop_bp)
app.register_blueprint(disease_bp)
app.register_blueprint(market_bp)
app.register_blueprint(profit_bp)
app.register_blueprint(assistant_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(notification_bp)

# --- Direct Marketplace & Equipment Rental Endpoints ---

@app.route('/api/equipment', methods=['GET'])
def list_equipment():
    try:
        items = Equipment.query.order_by(Equipment.id.asc()).all()
        data = [
            {
                "id": item.id,
                "name": item.name,
                "type": item.type,
                "owner": item.owner,
                "rate_per_hour": float(item.rate_per_hour) if item.rate_per_hour is not None else 0.0,
                "rate_per_day": float(item.rate_per_day) if item.rate_per_day is not None else 0.0,
                "location": item.location,
                "phone": item.phone,
                "image_url": item.image_url,
                "availability": bool(item.availability),
            }
            for item in items
        ]
        return jsonify({"success": True, "equipment": data})
    except Exception as error:
        current_app.logger.exception("Failed to list equipment")
        return jsonify({"success": False, "message": "Unable to list equipment."}), 500

@app.route('/api/equipment', methods=['POST'])
def add_equipment():
    data = request.get_json() or {}
    name = data.get('name')
    eq_type = data.get('type')
    owner = data.get('owner')
    rate_per_hour = data.get('rate_per_hour')
    rate_per_day = data.get('rate_per_day')
    location = data.get('location')
    phone = data.get('phone')
    image_url = data.get('image_url', '')

    if not name or not eq_type or not owner or rate_per_hour is None or rate_per_day is None or not location or not phone:
        return jsonify({"success": False, "message": "Missing required parameters."}), 400

    try:
        rate_per_hour = float(rate_per_hour)
        rate_per_day = float(rate_per_day)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Rates must be numbers."}), 400

    try:
        equipment = Equipment(
            name=name,
            type=eq_type,
            owner=owner,
            rate_per_hour=rate_per_hour,
            rate_per_day=rate_per_day,
            location=location,
            phone=phone,
            image_url=image_url,
            availability=True,
        )
        db.session.add(equipment)
        db.session.commit()
        return jsonify({"success": True, "message": "Equipment listing added successfully!"}), 201
    except Exception as error:
        db.session.rollback()
        current_app.logger.exception("Failed to add equipment")
        return jsonify({"success": False, "message": "Unable to add equipment listing."}), 500

@app.route('/api/equipment/book', methods=['POST'])
def book_equipment():
    data = request.get_json() or {}
    raw_user_id = data.get('user_id')
    user_id = parse_uuid(raw_user_id)
    equipment_id = data.get('equipment_id')
    hours = data.get('hours', 1)
    booking_date = data.get('date', '')

    if not equipment_id or not booking_date:
        return jsonify({"success": False, "message": "Missing booking parameters."}), 400

    try:
        hours = int(hours)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Hours must be a number."}), 400

    equipment = db.session.get(Equipment, equipment_id)
    if not equipment:
        return jsonify({"success": False, "message": "Equipment not found."}), 404

    if not equipment.availability:
        return jsonify({"success": False, "message": "Equipment is currently booked or unavailable."}), 400

    try:
        total_cost = float(equipment.rate_per_hour or 0.0) * hours
        booking = Booking(
            user_id=user_id,
            equipment_id=equipment_id,
            hours=hours,
            total_cost=total_cost,
            status='approved',
            date=booking_date,
        )
        equipment.availability = False
        db.session.add(booking)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Equipment booked successfully!",
            "total_cost": total_cost
        }), 201
    except Exception as error:
        db.session.rollback()
        current_app.logger.exception("Failed to book equipment")
        return jsonify({"success": False, "message": "Unable to book equipment."}), 500

@app.route('/api/equipment/history', methods=['GET'])
def booking_history():
    raw_user_id = request.args.get('user_id')
    user_id = parse_uuid(raw_user_id)
    try:
        query = Booking.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        bookings = (
            query.outerjoin(Equipment, Booking.equipment_id == Equipment.id)
            .order_by(Booking.created_at.desc())
            .all()
        )
        history = [
            {
                "id": booking.id,
                "user_id": str(booking.user_id) if booking.user_id else None,
                "equipment_name": booking.equipment.name if booking.equipment else None,
                "type": booking.equipment.type if booking.equipment else None,
                "hours": booking.hours,
                "total_cost": float(booking.total_cost or 0.0),
                "status": booking.status,
                "date": booking.date,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
            }
            for booking in bookings
        ]
        return jsonify({"success": True, "bookings": history})
    except Exception as error:
        current_app.logger.exception("Failed to load booking history")
        return jsonify({"success": False, "message": "Unable to load booking history."}), 500

@app.route('/api/products', methods=['GET'])
def list_products():
    try:
        products = Product.query.order_by(Product.id.asc()).all()
        data = [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": float(product.price or 0.0),
                "category": product.category,
                "image_url": product.image_url,
                "stock": product.stock,
            }
            for product in products
        ]
        return jsonify({"success": True, "products": data})
    except Exception as error:
        current_app.logger.exception("Failed to list products")
        return jsonify({"success": False, "message": "Unable to list products."}), 500

@app.route('/api/products/order', methods=['POST'])
def place_order():
    data = request.get_json() or {}
    raw_user_id = data.get('user_id')
    user_id = parse_uuid(raw_user_id)
    product_id = data.get('product_id')
    qty = data.get('quantity', 1)
    address = data.get('address', 'Direct Farm Delivery')

    if not product_id:
        return jsonify({"success": False, "message": "Missing product details."}), 400

    try:
        qty = int(qty)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Quantity must be a number."}), 400

    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"success": False, "message": "Product not found."}), 404

    if product.stock is None or product.stock < qty:
        return jsonify({"success": False, "message": f"Insufficient stock. Only {product.stock or 0} items available."}), 400

    try:
        total_cost = float(product.price or 0.0) * qty
        order = Order(
            user_id=user_id,
            product_id=product_id,
            quantity=qty,
            total_cost=total_cost,
            status='shipped',
            address=address,
        )
        product.stock = product.stock - qty
        db.session.add(order)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Order placed successfully! Standard delivery will reach within 48 hours.",
            "total_cost": total_cost
        }), 201
    except Exception as error:
        db.session.rollback()
        current_app.logger.exception("Failed to place order")
        return jsonify({"success": False, "message": "Unable to place order."}), 500

@app.route('/api/products/orders', methods=['GET'])
def order_history():
    raw_user_id = request.args.get('user_id')
    user_id = parse_uuid(raw_user_id)
    try:
        query = Order.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        orders = (
            query.outerjoin(Product, Order.product_id == Product.id)
            .order_by(Order.created_at.desc())
            .all()
        )
        response = [
            {
                "id": order.id,
                "user_id": str(order.user_id) if order.user_id else None,
                "product_name": order.product.name if order.product else None,
                "quantity": order.quantity,
                "total_cost": float(order.total_cost or 0.0),
                "status": order.status,
                "address": order.address,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }
            for order in orders
        ]
        return jsonify({"success": True, "orders": response})
    except Exception as error:
        current_app.logger.exception("Failed to load order history")
        return jsonify({"success": False, "message": "Unable to load order history."}), 500


@app.route('/api/listings', methods=['GET'])
def get_listings():
    category = request.args.get('category', '')
    search = request.args.get('search', '')

    try:
        query = Listing.query
        if category and category != 'All':
            query = query.filter_by(category=category)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Listing.title.ilike(search_pattern),
                    Listing.description.ilike(search_pattern),
                    Listing.location.ilike(search_pattern),
                )
            )

        listings = query.order_by(Listing.created_at.desc()).all()
        data = [
            {
                "id": listing.id,
                "user_id": str(listing.user_id) if listing.user_id else None,
                "category": listing.category,
                "title": listing.title,
                "description": listing.description,
                "price": float(listing.price or 0.0),
                "unit": listing.unit,
                "location": listing.location,
                "quantity": str(listing.quantity or ""),
                "phone": listing.phone,
                "created_at": listing.created_at.isoformat() if listing.created_at else None,
            }
            for listing in listings
        ]
        return jsonify({"success": True, "listings": data})
    except Exception as error:
        current_app.logger.exception("Failed to load listings")
        return jsonify({"success": False, "message": "Unable to load listings."}), 500


@app.route('/api/listings', methods=['POST'])
def create_listing():
    data = request.get_json() or {}
    category = data.get('category')
    title = data.get('title')
    description = data.get('description', '')
    price = data.get('price')
    unit = data.get('unit', 'quintal')
    location = data.get('location')
    quantity = data.get('quantity')
    phone = data.get('phone')
    raw_user_id = data.get('user_id')
    user_id = parse_uuid(raw_user_id)
    
    if not category or not title or price is None or not location or quantity is None or not phone:
        return jsonify({"success": False, "message": "Missing required listing parameters."}), 400
        
    try:
        price = float(price)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Price must be a number."}), 400

    try:
        listing = Listing(
            user_id=user_id,
            category=category,
            title=title,
            description=description,
            price=price,
            unit=unit,
            location=location,
            quantity=str(quantity),
            phone=phone,
        )
        db.session.add(listing)
        db.session.commit()
        return jsonify({"success": True, "message": "Listing created successfully!"}), 201
    except Exception as error:
        db.session.rollback()
        current_app.logger.exception("Failed to create listing")
        return jsonify({"success": False, "message": "Unable to create listing."}), 500


# Serves uploaded files (like plant leaf snaps)
@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Root check
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"success": True, "status": "healthy", "service": "AgroAI Backend API"})


if __name__ == "__main__":

    if os.getenv("CREATE_TABLES_ON_STARTUP", "false").lower() == "true":
        with app.app_context():
            db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True)