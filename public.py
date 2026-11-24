from flask import Blueprint, current_app, jsonify, request, abort
from sqlalchemy import or_
from extensions import db, limiter
from models import Vehicle, VehicleImage, Enquiry
import re

public_bp = Blueprint("public", __name__)

@public_bp.get("/api/vehicles")
def vehicles():
    query = Vehicle.query.filter_by(published=True)
    status = request.args.get("status", "available")
    if status in {"available", "reserved", "sold"}:
        query = query.filter_by(status=status)
    if request.args.get("make"):
        query = query.filter(Vehicle.make.ilike("%" + request.args["make"][:80] + "%"))
    if request.args.get("q"):
        term = "%" + request.args["q"][:100] + "%"
        query = query.filter(or_(Vehicle.name.ilike(term), Vehicle.make.ilike(term), Vehicle.model.ilike(term), Vehicle.description.ilike(term)))
    for key, column in (("year", Vehicle.year),):
        if request.args.get(key, "").isdigit():
            query = query.filter(column == int(request.args[key]))
    if request.args.get("max_price", "").isdigit():
        query = query.filter(Vehicle.price <= int(request.args["max_price"]))
    if request.args.get("max_mileage", "").isdigit():
        query = query.filter(Vehicle.mileage <= int(request.args["max_mileage"]))
    for key, column in (("transmission", Vehicle.transmission), ("fuel", Vehicle.fuel), ("condition", Vehicle.condition), ("body", Vehicle.body), ("model", Vehicle.model)):
        if request.args.get(key):
            query = query.filter(column.ilike(request.args[key][:80]))
    return jsonify({"vehicles": [item.to_dict() for item in query.order_by(Vehicle.featured.desc(), Vehicle.created_at.desc()).limit(200).all()]})

@public_bp.get("/api/vehicles/<string:slug>")
def vehicle_detail(slug):
    item = Vehicle.query.filter_by(slug=slug, published=True).first_or_404()
    return jsonify({"vehicle": item.to_dict()})

@public_bp.post("/api/enquiries")
@limiter.limit("5 per hour")
def create_enquiry():
    payload = request.get_json(silent=True) or request.form
    # Honeypot field: bots should leave this empty.
    if str(payload.get("website", "")).strip():
        return jsonify({"ok": True, "message": "Thank you. Your enquiry has been received."}), 202
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    phone = str(payload.get("phone", "")).strip()
    message = str(payload.get("message", "")).strip()
    slug = str(payload.get("vehicle_id", "")).strip()
    if not name or len(name) > 120 or not email or len(email) > 255 or not re.fullmatch(r"[^\\s@]+@[^\\s@]+\\.[^\\s@]+", email):
        return jsonify({"ok": False, "error": "Enter a valid name and email address."}), 400
    if not phone or len(phone) > 40 or not message or len(message) > 5000:
        return jsonify({"ok": False, "error": "Enter a phone number and a message under 5,000 characters."}), 400
    vehicle = Vehicle.query.filter_by(slug=slug).first() if slug else None
    if slug and not vehicle:
        return jsonify({"ok": False, "error": "That vehicle could not be found."}), 404
    enquiry = Enquiry(vehicle=vehicle, customer_name=name, email=email, phone=phone, message=message)
    db.session.add(enquiry)
    db.session.commit()
    return jsonify({"ok": True, "message": "Your enquiry has been received. Our team will be in touch."}), 201
