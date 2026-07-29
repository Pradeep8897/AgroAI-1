import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from backend.extensions import limiter
from backend.utils.jwt_handler import require_auth
# Import database initializer
from backend.database.mysql_connection import init_db, get_connection

# Import Blueprints
from backend.routes.auth import auth_bp
from backend.routes.crop import crop_bp
from backend.routes.disease import disease_bp
from backend.routes.market import market_bp
from backend.routes.profit import profit_bp
from backend.routes.assistant import assistant_bp
from backend.routes.admin import admin_bp
from backend.routes.notification import notification_bp
app = Flask(__name__)

# CORS Configuration
# Read allowed origins from environment but sanitize wildcards to prevent open CORS
allowed_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "http://127.0.0.1:5173").split(",")
# Prevent a wildcard '*' from being used accidentally in production
if any(o.strip() == '*' for o in allowed_origins):
    # Replace wildcard with a safe default (localhost dev origin)
    allowed_origins = [os.environ.get('CORS_SAFE_DEFAULT', 'http://127.0.0.1:5173')]
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

# Initialize rate limiter
limiter.init_app(app)

@app.after_request
def set_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'")
    return response

@app.route("/")
def home():
    return {
        "status": "success",
        "message": "AgroAI Backend Running"
    }

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
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM equipment ORDER BY id ASC")
        rows = cursor.fetchall()
        if is_sqlite:
            data = [dict(r) for r in rows]
        else:
            data = [{
                "id": r[0],
                "name": r[1],
                "type": r[2],
                "owner": r[3],
                "rate_per_hour": r[4],
                "rate_per_day": r[5],
                "location": r[6],
                "phone": r[7],
                "image_url": r[8],
                "availability": r[9]
            } for r in rows]
        return jsonify({"success": True, "equipment": data})
    finally:
        conn.close()

@app.route('/api/equipment', methods=['POST'])
@require_auth(allowed_roles=['user', 'farmer', 'expert', 'admin'])
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
    except ValueError:
        return jsonify({"success": False, "message": "Rates must be numbers."}), 400
        
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    try:
        if is_sqlite:
            cursor.execute(
                "INSERT INTO equipment (name, type, owner, rate_per_hour, rate_per_day, location, phone, image_url, availability) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
                (name, eq_type, owner, rate_per_hour, rate_per_day, location, phone, image_url)
            )
        else:
            cursor.execute(
                "INSERT INTO equipment (name, type, owner, rate_per_hour, rate_per_day, location, phone, image_url, availability) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)",
                (name, eq_type, owner, rate_per_hour, rate_per_day, location, phone, image_url)
            )
        conn.commit()
        return jsonify({"success": True, "message": "Equipment listing added successfully!"}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/equipment/book', methods=['POST'])
@require_auth(allowed_roles=['user', 'farmer', 'expert', 'admin'])
def book_equipment():
    data = request.get_json() or {}
    user_id = request.user_id
    equipment_id = data.get('equipment_id')
    hours = int(data.get('hours', 1))
    booking_date = data.get('date', '')

    if not user_id or not equipment_id or not booking_date:
        return jsonify({"success": False, "message": "Missing booking parameters."}), 400

    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    try:
        # Check rate
        if is_sqlite:
            cursor.execute("SELECT rate_per_hour, availability FROM equipment WHERE id = ?", (equipment_id,))
        else:
            cursor.execute("SELECT rate_per_hour, availability FROM equipment WHERE id = %s", (equipment_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Equipment not found."}), 404
        
        rate = row[0] if not is_sqlite else row['rate_per_hour']
        avail = row[1] if not is_sqlite else row['availability']
        
        if not avail:
            return jsonify({"success": False, "message": "Equipment is currently booked or unavailable."}), 400

        total_cost = rate * hours

        # Insert booking
        if is_sqlite:
            cursor.execute(
                "INSERT INTO bookings (user_id, equipment_id, hours, total_cost, status, date) VALUES (?, ?, ?, ?, 'approved', ?)",
                (user_id, equipment_id, hours, total_cost, booking_date)
            )
            # Toggle availability
            cursor.execute("UPDATE equipment SET availability = 0 WHERE id = ?", (equipment_id,))
        else:
            cursor.execute(
                "INSERT INTO bookings (user_id, equipment_id, hours, total_cost, status, date) VALUES (%s, %s, %s, %s, 'approved', %s)",
                (user_id, equipment_id, hours, total_cost, booking_date)
            )
            cursor.execute("UPDATE equipment SET availability = FALSE WHERE id = %s", (equipment_id,))

        conn.commit()
        return jsonify({
            "success": True,
            "message": "Equipment booked successfully!",
            "total_cost": total_cost
        }), 201
    finally:
        conn.close()

@app.route('/api/equipment/history', methods=['GET'])
@require_auth(allowed_roles=['user', 'farmer', 'expert', 'admin'])
def booking_history():
    user_id = request.user_id
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    try:
        if is_sqlite:
            cursor.execute("""
                SELECT b.id, e.name as equipment_name, e.type, b.hours, b.total_cost, b.status, b.date, b.created_at 
                FROM bookings b 
                JOIN equipment e ON b.equipment_id = e.id 
                WHERE b.user_id = ?
                ORDER BY b.created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            history = [dict(r) for r in rows]
        else:
            cursor.execute("""
                SELECT b.id, e.name as equipment_name, e.type, b.hours, b.total_cost, b.status, b.date, b.created_at 
                FROM bookings b 
                JOIN equipment e ON b.equipment_id = e.id 
                WHERE b.user_id = %s
                ORDER BY b.created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            history = [{
                "id": r[0],
                "equipment_name": r[1],
                "type": r[2],
                "hours": r[3],
                "total_cost": r[4],
                "status": r[5],
                "date": r[6],
                "created_at": r[7]
            } for r in rows]
        return jsonify({"success": True, "bookings": history})
    finally:
        conn.close()

@app.route('/api/products', methods=['GET'])
def list_products():
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()
        if is_sqlite:
            data = [dict(r) for r in rows]
        else:
            data = [{
                "id": r[0],
                "name": r[1],
                "description": r[2],
                "price": r[3],
                "category": r[4],
                "image_url": r[5],
                "stock": r[6]
            } for r in rows]
        return jsonify({"success": True, "products": data})
    finally:
        conn.close()

@app.route('/api/products/order', methods=['POST'])
@require_auth(allowed_roles=['user', 'farmer', 'expert', 'admin'])
def place_order():
    data = request.get_json() or {}
    user_id = request.user_id
    product_id = data.get('product_id')
    qty = int(data.get('quantity', 1))
    address = data.get('address', 'Direct Farm Delivery')

    if not user_id or not product_id:
        return jsonify({"success": False, "message": "Missing product or user details."}), 400

    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    try:
        # Check stock & price
        if is_sqlite:
            cursor.execute("SELECT price, stock FROM products WHERE id = ?", (product_id,))
        else:
            cursor.execute("SELECT price, stock FROM products WHERE id = %s", (product_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Product not found."}), 404

        price = row[0] if not is_sqlite else row['price']
        stock = row[1] if not is_sqlite else row['stock']

        if stock < qty:
            return jsonify({"success": False, "message": f"Insufficient stock. Only {stock} items available."}), 400

        total_cost = price * qty

        # Insert order
        if is_sqlite:
            cursor.execute(
                "INSERT INTO orders (user_id, product_id, quantity, total_cost, status, address) VALUES (?, ?, ?, ?, 'shipped', ?)",
                (user_id, product_id, qty, total_cost, address)
            )
            # Deduct stock
            cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, product_id))
        else:
            cursor.execute(
                "INSERT INTO orders (user_id, product_id, quantity, total_cost, status, address) VALUES (%s, %s, %s, %s, 'shipped', %s)",
                (user_id, product_id, qty, total_cost, address)
            )
            cursor.execute("UPDATE products SET stock = stock - %s WHERE id = %s", (qty, product_id))

        conn.commit()
        return jsonify({
            "success": True,
            "message": "Order placed successfully! Standard delivery will reach within 48 hours.",
            "total_cost": total_cost
        }), 201
    finally:
        conn.close()

@app.route('/api/products/orders', methods=['GET'])
@require_auth(allowed_roles=['user', 'farmer', 'expert', 'admin'])
def order_history():
    user_id = request.user_id
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    try:
        if is_sqlite:
            cursor.execute("""
                SELECT o.id, p.name as product_name, o.quantity, o.total_cost, o.status, o.address, o.created_at 
                FROM orders o 
                JOIN products p ON o.product_id = p.id 
                WHERE o.user_id = ?
                ORDER BY o.created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            orders = [dict(r) for r in rows]
        else:
            cursor.execute("""
                SELECT o.id, p.name as product_name, o.quantity, o.total_cost, o.status, o.address, o.created_at 
                FROM orders o 
                JOIN products p ON o.product_id = p.id 
                WHERE o.user_id = %s
                ORDER BY o.created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            orders = [{
                "id": r[0],
                "product_name": r[1],
                "quantity": r[2],
                "total_cost": r[3],
                "status": r[4],
                "address": r[5],
                "created_at": r[6]
            } for r in rows]
        return jsonify({"success": True, "orders": orders})
    finally:
        conn.close()


@app.route('/api/listings', methods=['GET'])
def get_listings():
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM listings"
        params = []
        conditions = []
        
        if category and category != 'All':
            conditions.append("category = ?") if is_sqlite else conditions.append("category = %s")
            params.append(category)
            
        if search:
            conditions.append("(title LIKE ? OR description LIKE ? OR location LIKE ?)") if is_sqlite else conditions.append("(title LIKE %s OR description LIKE %s OR location LIKE %s)")
            params.append(f"%{search}%")
            params.append(f"%{search}%")
            params.append(f"%{search}%")
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        if is_sqlite:
            data = [dict(r) for r in rows]
        else:
            data = [{
                "id": r[0],
                "user_id": r[1],
                "category": r[2],
                "title": r[3],
                "description": r[4],
                "price": r[5],
                "unit": r[6],
                "location": r[7],
                "quantity": r[8],
                "phone": r[9],
                "created_at": r[10]
            } for r in rows]
            
        return jsonify({"success": True, "listings": data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/listings', methods=['POST'])
@require_auth(allowed_roles=['user', 'farmer', 'expert', 'admin'])
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
    user_id = request.user_id
    
    if not category or not title or price is None or not location or not quantity or not phone:
        return jsonify({"success": False, "message": "Missing required listing parameters."}), 400
        
    try:
        price = float(price)
    except ValueError:
        return jsonify({"success": False, "message": "Price must be a number."}), 400
        
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    try:
        if is_sqlite:
            cursor.execute(
                "INSERT INTO listings (user_id, category, title, description, price, unit, location, quantity, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, category, title, description, price, unit, location, quantity, phone)
            )
        else:
            cursor.execute(
                "INSERT INTO listings (user_id, category, title, description, price, unit, location, quantity, phone) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (user_id, category, title, description, price, unit, location, quantity, phone)
            )
        conn.commit()
        return jsonify({"success": True, "message": "Listing created successfully!"}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()


# Serves uploaded files (like plant leaf snaps)
@app.route('/api/uploads/<filename>')
@require_auth(allowed_roles=['user', 'farmer', 'expert', 'admin'])
def uploaded_file(filename):
    # Require authenticated users to download uploaded files
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



# Root check
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"success": True, "status": "healthy", "service": "AgroAI Backend API"})

# Seeding utility trigger
@app.route('/api/db/init', methods=['POST'])
@require_auth(allowed_roles=['admin'])
def run_init_db():
    try:
        init_db()
        return jsonify({"success": True, "message": "Database successfully initialized/seeded."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    # Initialize DB schemas on launch
    init_db()
    
    # Run server
    app.run(host='0.0.0.0', port=5000, debug=True)
