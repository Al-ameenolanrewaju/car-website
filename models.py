from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager

def utcnow():
    return datetime.now(timezone.utc)

class AdminUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False, default="Administrator")
    role = db.Column(db.String(30), nullable=False, default="admin")
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_login_at = db.Column(db.DateTime(timezone=True))
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    @property
    def is_active(self):
        return self.active

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(AdminUser, int(user_id))
    except (TypeError, ValueError):
        return None

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    make = db.Column(db.String(80), nullable=False, index=True)
    model = db.Column(db.String(100), nullable=False, index=True)
    name = db.Column(db.String(180), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    price = db.Column(db.Numeric(14, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="NGN")
    mileage = db.Column(db.Integer, nullable=False, default=0)
    mileage_unit = db.Column(db.String(8), nullable=False, default="km")
    transmission = db.Column(db.String(40), nullable=False)
    fuel = db.Column(db.String(40), nullable=False)
    condition = db.Column(db.String(20), nullable=False, default="used")
    body = db.Column(db.String(50), nullable=False)
    engine = db.Column(db.String(100), default="")
    drive = db.Column(db.String(100), default="")
    colour = db.Column(db.String(80), default="")
    description = db.Column(db.Text, default="")
    features_json = db.Column(db.Text, nullable=False, default="[]")
    status = db.Column(db.String(20), nullable=False, default="available", index=True)
    featured = db.Column(db.Boolean, nullable=False, default=False)
    published = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    images = db.relationship("VehicleImage", backref="vehicle", cascade="all, delete-orphan", order_by="VehicleImage.position")
    enquiries = db.relationship("Enquiry", backref="vehicle", lazy="dynamic")
    @property
    def features(self):
        import json
        try:
            value = json.loads(self.features_json or "[]")
            return value if isinstance(value, list) else []
        except (ValueError, TypeError):
            return []
    def to_dict(self):
        return {
            "id": self.slug, "slug": self.slug, "make": self.make, "model": self.model,
            "name": self.name, "year": self.year, "price": float(self.price),
            "currency": self.currency, "mileage": self.mileage, "mileageUnit": self.mileage_unit,
            "transmission": self.transmission, "fuel": self.fuel, "condition": self.condition,
            "body": self.body, "engine": self.engine or "", "drive": self.drive or "",
            "colour": self.colour or "", "description": self.description or "",
            "features": self.features, "status": self.status, "featured": self.featured,
            "tag": "Featured" if self.featured else ("Sold" if self.status == "sold" else ("Reserved" if self.status == "reserved" else ("New arrival" if self.condition == "new" else "Available"))),
            "images": [image.url for image in self.images]
        }

class VehicleImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(80), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    @property
    def url(self):
        return "/media/" + str(self.id)

enquiry_vehicles = db.Table(
    "enquiry_vehicles",
    db.Column("enquiry_id", db.Integer, db.ForeignKey("enquiry.id", ondelete="CASCADE"), primary_key=True),
    db.Column("vehicle_id", db.Integer, db.ForeignKey("vehicle.id", ondelete="CASCADE"), primary_key=True),
)

class Enquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id", ondelete="SET NULL"), index=True)
    selected_vehicles = db.relationship("Vehicle", secondary=enquiry_vehicles, lazy="select")
    customer_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="new", index=True)
    source = db.Column(db.String(40), nullable=False, default="website")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False, default="")
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin_user.id", ondelete="SET NULL"))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(60), nullable=False)
    entity_id = db.Column(db.String(100))
    detail = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

def record_audit(action, entity_type, entity_id=None, detail=""):
    from flask_login import current_user
    admin_id = current_user.id if current_user.is_authenticated else None
    db.session.add(AuditLog(admin_id=admin_id, action=action, entity_type=entity_type, entity_id=str(entity_id or ""), detail=detail))
