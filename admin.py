import json
import re
from decimal import Decimal, InvalidOperation
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db, limiter
from models import AdminUser, Vehicle, VehicleImage, Enquiry, SiteSetting, AuditLog, record_audit

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
ALLOWED_IMAGES = {"image/jpeg", "image/png", "image/webp", "image/avif"}

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role not in {"admin", "manager"}:
            abort(403)
        return fn(*args, **kwargs)
    return wrapped

@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("8 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = AdminUser.query.filter_by(email=email, active=True).first()
        if user and user.check_password(password):
            login_user(user, remember=False, fresh=True)
            from models import utcnow
            user.last_login_at = utcnow()
            db.session.commit()
            return redirect(request.args.get("next") if request.args.get("next", "").startswith("/admin") else url_for("admin.dashboard"))
        flash("Email or password is incorrect.", "error")
    return render_template("admin/login.html")

@admin_bp.post("/logout")
@admin_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("admin.login"))

@admin_bp.get("/")
@admin_required
def dashboard():
    from sqlalchemy import func
    stats = {
        "total": Vehicle.query.count(),
        "available": Vehicle.query.filter_by(status="available").count(),
        "reserved": Vehicle.query.filter_by(status="reserved").count(),
        "sold": Vehicle.query.filter_by(status="sold").count(),
        "enquiries": Enquiry.query.count(),
        "new_enquiries": Enquiry.query.filter_by(status="new").count(),
        "team": AdminUser.query.count(),
    }
    recent = Enquiry.query.order_by(Enquiry.created_at.desc()).limit(6).all()
    latest = Vehicle.query.order_by(Vehicle.created_at.desc()).limit(5).all()
    activity = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()
    return render_template("admin/dashboard.html", stats=stats, recent=recent, latest=latest, activity=activity)

@admin_bp.get("/vehicles")
@admin_required
def vehicles():
    search = request.args.get("q", "").strip()[:100]
    query = Vehicle.query
    if search:
        query = query.filter(Vehicle.name.ilike("%" + search + "%"))
    status = request.args.get("status", "")
    if status in {"available", "reserved", "sold"}:
        query = query.filter_by(status=status)
    items = query.order_by(Vehicle.updated_at.desc()).all()
    return render_template("admin/vehicles.html", vehicles=items, search=search, status=status)

def vehicle_values(form):
    required = ["make", "model", "name", "year", "price", "transmission", "fuel", "condition", "body"]
    values = {key: form.get(key, "").strip() for key in required}
    if any(not values[key] for key in required):
        raise ValueError("Complete all required vehicle fields.")
    if not values["year"].isdigit() or not 1886 <= int(values["year"]) <= 2100:
        raise ValueError("Enter a valid vehicle year.")
    try:
        price = Decimal(values["price"].replace(",", ""))
        if price <= 0 or price > Decimal("999999999999"):
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid positive vehicle price.")
    mileage = form.get("mileage", "0").strip() or "0"
    if not mileage.isdigit() or int(mileage) < 0:
        raise ValueError("Mileage must be a non-negative whole number.")
    features = [part.strip()[:100] for part in form.get("features", "").splitlines() if part.strip()][:40]
    return {
        "make": values["make"][:80], "model": values["model"][:100], "name": values["name"][:180],
        "year": int(values["year"]), "price": price, "currency": form.get("currency", "NGN")[:3].upper(),
        "mileage": int(mileage), "mileage_unit": form.get("mileage_unit", "km")[:8],
        "transmission": values["transmission"][:40], "fuel": values["fuel"][:40],
        "condition": values["condition"] if values["condition"] in {"new", "used"} else "used",
        "body": values["body"][:50], "engine": form.get("engine", "")[:100],
        "drive": form.get("drive", "")[:100], "colour": form.get("colour", "")[:80],
        "description": form.get("description", "")[:10000], "features_json": json.dumps(features),
        "status": form.get("status", "available") if form.get("status") in {"available", "reserved", "sold"} else "available",
        "featured": form.get("featured") == "on", "published": form.get("published") == "on"
    }

def make_slug(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:150] or "vehicle"
    base, suffix = slug, 2
    while Vehicle.query.filter_by(slug=slug).first():
        slug = base + "-" + str(suffix)
        suffix += 1
    return slug

def save_uploads(vehicle):
    uploads = request.files.getlist("images")
    current = len(vehicle.images)
    for upload in uploads:
        if not upload or not upload.filename:
            continue
        if upload.mimetype not in ALLOWED_IMAGES:
            raise ValueError("Only JPEG, PNG, WebP and AVIF images are accepted.")
        data = upload.read(8 * 1024 * 1024 + 1)
        if not data or len(data) > 8 * 1024 * 1024:
            raise ValueError("Each image must be smaller than 8 MB.")
        signatures = {"image/jpeg": data.startswith(bytes.fromhex("ffd8ff")), "image/png": data.startswith(bytes.fromhex("89504e470d0a1a0a")), "image/webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP", "image/avif": b"ftypavif" in data[:32] or b"ftypavis" in data[:32]}
        if not signatures.get(upload.mimetype, False):
            raise ValueError("The uploaded file content does not match its image type.")
        image = VehicleImage(vehicle=vehicle, filename=secure_filename(upload.filename)[:255] or "vehicle-image", mime_type=upload.mimetype, data=data, position=current)
        db.session.add(image)
        current += 1
    if current > 20:
        raise ValueError("A vehicle can have at most 20 images.")

@admin_bp.route("/vehicles/new", methods=["GET", "POST"])
@admin_required
def vehicle_new():
    if request.method == "POST":
        try:
            vehicle = Vehicle(slug="pending-" + str(current_user.id), **vehicle_values(request.form))
            db.session.add(vehicle)
            db.session.flush()
            vehicle.slug = make_slug(vehicle.name)
            save_uploads(vehicle)
            record_audit("vehicle.created", "vehicle", vehicle.slug, vehicle.name)
            db.session.commit()
            flash("Vehicle added to your inventory.", "success")
            return redirect(url_for("admin.vehicle_edit", vehicle_id=vehicle.id))
        except (ValueError, Exception) as error:
            db.session.rollback()
            flash(str(error) if isinstance(error, ValueError) else "The vehicle could not be saved. Check the fields and try again.", "error")
    default_currency = SiteSetting.query.filter_by(key="currency").first()
    return render_template("admin/vehicle_form.html", vehicle=None, default_currency=default_currency.value if default_currency else "NGN")

@admin_bp.route("/vehicles/<int:vehicle_id>/edit", methods=["GET", "POST"])
@admin_required
def vehicle_edit(vehicle_id):
    vehicle = db.get_or_404(Vehicle, vehicle_id)
    if request.method == "POST":
        try:
            for key, value in vehicle_values(request.form).items():
                setattr(vehicle, key, value)
            for raw_id in request.form.getlist("remove_images"):
                if raw_id.isdigit():
                    image = VehicleImage.query.filter_by(id=int(raw_id), vehicle_id=vehicle.id).first()
                    if image:
                        vehicle.images.remove(image)
                        db.session.delete(image)
            db.session.flush()
            save_uploads(vehicle)
            record_audit("vehicle.updated", "vehicle", vehicle.slug, vehicle.name)
            db.session.commit()
            flash("Vehicle changes saved.", "success")
            return redirect(url_for("admin.vehicle_edit", vehicle_id=vehicle.id))
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
    default_currency = SiteSetting.query.filter_by(key="currency").first()
    return render_template("admin/vehicle_form.html", vehicle=vehicle, default_currency=default_currency.value if default_currency else "NGN")

@admin_bp.post("/vehicles/<int:vehicle_id>/delete")
@admin_required
def vehicle_delete(vehicle_id):
    vehicle = db.get_or_404(Vehicle, vehicle_id)
    record_audit("vehicle.deleted", "vehicle", vehicle.slug, vehicle.name)
    db.session.delete(vehicle)
    db.session.commit()
    flash("Vehicle removed.", "success")
    return redirect(url_for("admin.vehicles"))

@admin_bp.post("/images/<int:image_id>/delete")
@admin_required
def image_delete(image_id):
    image = db.get_or_404(VehicleImage, image_id)
    vehicle_id = image.vehicle_id
    db.session.delete(image)
    db.session.commit()
    flash("Image deleted.", "success")
    return redirect(url_for("admin.vehicle_edit", vehicle_id=vehicle_id))

@admin_bp.get("/enquiries")
@admin_required
def enquiries():
    status = request.args.get("status", "")
    query = Enquiry.query
    if status in {"new", "contacted", "closed"}:
        query = query.filter_by(status=status)
    items = query.order_by(Enquiry.created_at.desc()).all()
    return render_template("admin/enquiries.html", enquiries=items, status=status)

@admin_bp.post("/enquiries/<int:enquiry_id>/status")
@admin_required
def enquiry_status(enquiry_id):
    item = db.get_or_404(Enquiry, enquiry_id)
    status = request.form.get("status")
    if status not in {"new", "contacted", "closed"}:
        abort(400)
    item.status = status
    record_audit("enquiry.status_changed", "enquiry", item.id, status)
    db.session.commit()
    flash("Enquiry status updated.", "success")
    return redirect(url_for("admin.enquiries"))

@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    defaults = {"business_name": "Premier Motorworks", "contact_email": "", "whatsapp_number": "", "currency": "NGN", "address": ""}
    if request.method == "POST":
        for key in defaults:
            value = request.form.get(key, "").strip()[:255]
            item = SiteSetting.query.filter_by(key=key).first()
            if item is None:
                item = SiteSetting(key=key, value=value)
                db.session.add(item)
            else:
                item.value = value
        record_audit("settings.updated", "settings", "site")
        db.session.commit()
        flash("Business settings saved.", "success")
        return redirect(url_for("admin.settings"))
    values = defaults.copy()
    for item in SiteSetting.query.all():
        if item.key in values:
            values[item.key] = item.value
    return render_template("admin/settings.html", settings=values)

@admin_bp.get("/api/overview")
@admin_required
def overview_api():
    return jsonify({"vehicles": Vehicle.query.count(), "enquiries": Enquiry.query.count(), "new_enquiries": Enquiry.query.filter_by(status="new").count()})


@admin_bp.route("/team", methods=["GET", "POST"])
@admin_required
def team():
    if current_user.role != "admin":
        abort(403)
    if request.method == "POST":
        action = request.form.get("action", "create")
        if action == "create":
            email = request.form.get("email", "").strip().lower()
            name = request.form.get("name", "").strip()[:120]
            password = request.form.get("password", "")
            role = request.form.get("role", "manager")
            if not email or len(email) > 255 or "@" not in email or not name:
                flash("Enter a valid email address and team member name.", "error")
            elif len(password) < 1:
                flash("Use a temporary password with at least 1 character.", "error")
            elif role not in {"admin", "manager"}:
                abort(400)
            elif AdminUser.query.filter_by(email=email).first():
                flash("That email address already has an account.", "error")
            else:
                user = AdminUser(email=email, name=name, role=role, active=True)
                user.set_password(password)
                db.session.add(user)
                db.session.flush()
                record_audit("team.member_created", "admin_user", user.id, email)
                db.session.commit()
                flash("Team account created. Share the temporary password securely.", "success")
                return redirect(url_for("admin.team"))
        elif action == "update":
            raw_id = request.form.get("user_id", "")
            if not raw_id.isdigit():
                abort(400)
            user = db.get_or_404(AdminUser, int(raw_id))
            if user.id == current_user.id:
                flash("You cannot change your own access from this screen.", "error")
            else:
                new_role = request.form.get("role", user.role)
                active = request.form.get("active") == "on"
                if new_role not in {"admin", "manager"}:
                    abort(400)
                if user.active and user.role == "admin" and (not active or new_role != "admin"):
                    other_admins = AdminUser.query.filter_by(active=True, role="admin").filter(AdminUser.id != user.id).count()
                    if other_admins == 0:
                        flash("The account must keep at least one active administrator.", "error")
                        return redirect(url_for("admin.team"))
                user.role = new_role
                user.active = active
                record_audit("team.member_updated", "admin_user", user.id, "role=" + new_role + "; active=" + str(active))
                db.session.commit()
                flash("Team access updated.", "success")
                return redirect(url_for("admin.team"))
    members = AdminUser.query.order_by(AdminUser.created_at.asc()).all()
    return render_template("admin/team.html", members=members)
