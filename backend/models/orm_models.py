from extensions import db
from sqlalchemy.dialects.postgresql import UUID
import uuid


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="farmer")
    phone = db.Column(db.String(50))
    location = db.Column(db.String(255))
    state = db.Column(db.String(255))
    farm_size = db.Column(db.Numeric)
    language = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    crops = db.relationship("Crop", back_populates="user")
    disease_reports = db.relationship("DiseaseReport", back_populates="user")
    bookings = db.relationship("Booking", back_populates="user")
    listings = db.relationship("Listing", back_populates="user")
    orders = db.relationship("Order", back_populates="user")
    notifications = db.relationship("Notification", back_populates="user")
    chat_history = db.relationship("ChatHistory", back_populates="user")
    login_attempts = db.relationship("LoginAttempt", back_populates="user")
    login_sessions = db.relationship("LoginSession", back_populates="user")


class Crop(db.Model):
    __tablename__ = "crops"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    name = db.Column(db.String(255), nullable=False)
    N = db.Column("n", db.Integer)
    P = db.Column("p", db.Integer)
    K = db.Column("k", db.Integer)
    ph = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    prediction = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    user = db.relationship("User", back_populates="crops")


class Disease(db.Model):
    __tablename__ = "diseases"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    severity = db.Column(db.String(100))
    cause = db.Column(db.Text)
    chemical_cure = db.Column(db.Text)
    organic_cure = db.Column(db.Text)


class DiseaseReport(db.Model):
    __tablename__ = "disease_reports"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    crop_name = db.Column(db.String(255))
    disease_name = db.Column(db.String(255))
    severity = db.Column(db.String(100))
    image_path = db.Column(db.String(255))
    status = db.Column(db.String(100), nullable=False, default="pending", server_default="pending")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    user = db.relationship("User", back_populates="disease_reports")


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric)
    category = db.Column(db.String(255))
    image_url = db.Column(db.Text)
    stock = db.Column(db.Integer, nullable=False, default=10, server_default="10")

    orders = db.relationship("Order", back_populates="product")


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    product_id = db.Column(db.BigInteger, db.ForeignKey("products.id", ondelete="SET NULL"))
    quantity = db.Column(db.Integer)
    total_cost = db.Column(db.Numeric)
    status = db.Column(db.String(100), nullable=False, default="pending", server_default="pending")
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    user = db.relationship("User", back_populates="orders")
    product = db.relationship("Product", back_populates="orders")


class Equipment(db.Model):
    __tablename__ = "equipment"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255))
    owner = db.Column(db.String(255))
    rate_per_hour = db.Column(db.Numeric)
    rate_per_day = db.Column(db.Numeric)
    location = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    image_url = db.Column(db.Text)
    availability = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())

    bookings = db.relationship("Booking", back_populates="equipment")


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    equipment_id = db.Column(db.BigInteger, db.ForeignKey("equipment.id", ondelete="SET NULL"))
    hours = db.Column(db.Integer)
    total_cost = db.Column(db.Numeric)
    status = db.Column(db.String(100), nullable=False, default="pending", server_default="pending")
    date = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    user = db.relationship("User", back_populates="bookings")
    equipment = db.relationship("Equipment", back_populates="bookings")


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    category = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric, nullable=False)
    unit = db.Column(db.String(100), nullable=False, default="quintal", server_default="quintal")
    location = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    user = db.relationship("User", back_populates="listings")


class MarketPrice(db.Model):
    __tablename__ = "market_prices"

    id = db.Column(db.BigInteger, primary_key=True)
    crop_name = db.Column(db.String(255), nullable=False)
    market_name = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(255), nullable=False)
    current_price = db.Column(db.Numeric)
    predicted_price = db.Column(db.Numeric)
    date = db.Column(db.String(100))


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(100))
    date = db.Column(db.String(100))
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    user = db.relationship("User", back_populates="notifications")


class ChatHistory(db.Model):
    __tablename__ = "chat_history"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    sender = db.Column(db.String(100))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    user = db.relationship("User", back_populates="chat_history")


class LoginAttempt(db.Model):
    __tablename__ = "login_attempts"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    email = db.Column(db.String(255))
    success = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    user = db.relationship("User", back_populates="login_attempts")


class LoginSession(db.Model):
    __tablename__ = "login_sessions"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_token = db.Column(db.Text)
    active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    last_activity_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    user = db.relationship("User", back_populates="login_sessions")
