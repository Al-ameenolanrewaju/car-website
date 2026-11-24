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
    elif status != "all":
        query = query.filter_by(status="available")
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
    raw_ids = payload.get("vehicle_ids", None)
    if raw_ids is None:
        legacy_id = str(payload.get("vehicle_id", "")).strip()
        requested_ids = [legacy_id] if legacy_id else []
    else:
        if not isinstance(raw_ids, (list, tuple)) or not raw_ids or len(raw_ids) > 10:
            return jsonify({"ok": False, "error": "Choose between 1 and 10 vehicles for a combined enquiry."}), 400
        requested_ids = [str(value).strip() for value in raw_ids]
        if any(not value for value in requested_ids) or len(set(requested_ids)) != len(requested_ids):
            return jsonify({"ok": False, "error": "The vehicle selection contains an invalid or duplicate entry."}), 400

    if not name or len(name) > 120 or not email or len(email) > 255 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return jsonify({"ok": False, "error": "Enter a valid name and email address."}), 400
    if not phone or len(phone) > 40 or not message or len(message) > 5000:
        return jsonify({"ok": False, "error": "Enter a phone number and a message under 5,000 characters."}), 400

    selected = []
    if requested_ids:
        selected = Vehicle.query.filter(
            Vehicle.slug.in_(requested_ids),
            Vehicle.published.is_(True),
            Vehicle.status == "available"
        ).all()
        found = {item.slug for item in selected}
        if found != set(requested_ids):
            return jsonify({"ok": False, "error": "One or more selected vehicles are unavailable. Refresh the collection and try again."}), 409
        selected.sort(key=lambda item: requested_ids.index(item.slug))

    enquiry = Enquiry(
        vehicle=selected[0] if selected else None,
        selected_vehicles=selected,
        customer_name=name, email=email, phone=phone, message=message
    )
    db.session.add(enquiry)
    db.session.commit()
    return jsonify({"ok": True, "message": "Your enquiry has been received. Our team will be in touch.", "enquiry_id": enquiry.id, "vehicle_count": len(selected)}), 201


@public_bp.get("/api/site-settings")
def public_site_settings():
    from models import SiteSetting
    values = {item.key: item.value for item in SiteSetting.query.filter(SiteSetting.key.in_(["business_name", "whatsapp_number", "currency", "instagram_url", "facebook_url", "tiktok_url", "x_url", "vehicle_categories"])).all()}
    return jsonify({"business_name": values.get("business_name", "Premier Motorworks"), "whatsapp_number": values.get("whatsapp_number", ""), "currency": values.get("currency", "NGN"), "instagram_url": values.get("instagram_url", ""), "facebook_url": values.get("facebook_url", ""), "tiktok_url": values.get("tiktok_url", ""), "x_url": values.get("x_url", ""), "vehicle_categories": [line.strip() for line in values.get("vehicle_categories", "Sedan\\nSUV\\nCoupe\\nHatchback\\nTruck\\nPickup\\nVan\\nConvertible\\nWagon\\nSports car").splitlines() if line.strip()]})
