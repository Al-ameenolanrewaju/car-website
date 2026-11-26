"""One-time, idempotent sample inventory seeder.

Run explicitly with:
    ENABLE_SAMPLE_VEHICLE_SEED=YES flask --app app seed-sample-vehicles

Only creates records in the configured app schema (cars on hosted deployment).
Existing vehicle records are never updated or deleted.
"""
import json
from decimal import Decimal

import click
from flask import current_app
from sqlalchemy import inspect, text

from extensions import db
from models import Vehicle, VehicleImage

# Public demo image URLs from images.unsplash.com. Downloaded and stored as
# binary VehicleImage rows so the site's existing /media/<id> pipeline works.
# Three distinct angles/images are assigned to each listing.
VEHICLES = [
    dict(make="Toyota", model="Camry XSE", year=2021, price="38500000", mileage=42000, transmission="Automatic", fuel="Petrol", body="Sedan", engine="2.5L 4-Cylinder", drive="FWD", colour="Pearl White", features=["Leather interior", "Apple CarPlay", "Blind-spot monitor", "Reverse camera"]),
    dict(make="Lexus", model="RX 350", year=2020, price="62500000", mileage=51000, transmission="Automatic", fuel="Petrol", body="SUV", engine="3.5L V6", drive="AWD", colour="Black", features=["Sunroof", "Leather seats", "Power tailgate", "Parking sensors"]),
    dict(make="Mercedes-Benz", model="C300", year=2019, price="46500000", mileage=58000, transmission="Automatic", fuel="Petrol", body="Sedan", engine="2.0L Turbo", drive="RWD", colour="Obsidian Black", features=["AMG styling", "Panoramic roof", "Ambient lighting", "Navigation"]),
    dict(make="BMW", model="X5 xDrive40i", year=2021, price="89500000", mileage=39000, transmission="Automatic", fuel="Petrol", body="SUV", engine="3.0L Turbo Inline-6", drive="AWD", colour="Mineral White", features=["xDrive AWD", "Panoramic roof", "Harman Kardon audio", "360 camera"]),
    dict(make="Honda", model="Accord Touring", year=2020, price="34200000", mileage=47000, transmission="Automatic", fuel="Petrol", body="Sedan", engine="2.0L Turbo", drive="FWD", colour="Modern Steel", features=["Adaptive cruise control", "Heated seats", "Lane keeping assist", "Wireless charging"]),
    dict(make="Toyota", model="Land Cruiser Prado", year=2018, price="73500000", mileage=69000, transmission="Automatic", fuel="Petrol", body="SUV", engine="4.0L V6", drive="4WD", colour="Silver", features=["Four-wheel drive", "Leather seats", "Rear camera", "Third-row seating"]),
    dict(make="Hyundai", model="Tucson Limited", year=2022, price="41500000", mileage=28000, transmission="Automatic", fuel="Petrol", body="SUV", engine="2.5L 4-Cylinder", drive="AWD", colour="Amazon Gray", features=["Panoramic sunroof", "Smart cruise control", "Blind-spot view", "Wireless CarPlay"]),
    dict(make="Kia", model="Sorento EX", year=2021, price="43800000", mileage=36000, transmission="Automatic", fuel="Petrol", body="SUV", engine="2.5L 4-Cylinder", drive="FWD", colour="Gravity Blue", features=["Three-row seating", "Smart key", "Rear camera", "Drive modes"]),
    dict(make="Lexus", model="ES 350", year=2019, price="49500000", mileage=54000, transmission="Automatic", fuel="Petrol", body="Sedan", engine="3.5L V6", drive="FWD", colour="Atomic Silver", features=["Mark Levinson audio", "Leather interior", "Sunroof", "Adaptive headlights"]),
    dict(make="Toyota", model="Corolla SE", year=2022, price="29800000", mileage=25000, transmission="Automatic", fuel="Petrol", body="Sedan", engine="2.0L 4-Cylinder", drive="FWD", colour="Blueprint", features=["Sport seats", "Apple CarPlay", "Toyota Safety Sense", "Rear camera"]),
    dict(make="Range Rover", model="Velar P250", year=2020, price="78500000", mileage=49000, transmission="Automatic", fuel="Petrol", body="SUV", engine="2.0L Turbo", drive="AWD", colour="Santorini Black", features=["Meridian audio", "Panoramic roof", "Touch Pro Duo", "Electric tailgate"]),
    dict(make="Audi", model="Q5 Premium Plus", year=2021, price="57200000", mileage=41000, transmission="Automatic", fuel="Petrol", body="SUV", engine="2.0L TFSI", drive="AWD", colour="Navarra Blue", features=["Quattro AWD", "Virtual cockpit", "Bang & Olufsen audio", "Parking assist"]),
    dict(make="Volkswagen", model="Golf GTI", year=2019, price="31500000", mileage=52000, transmission="Automatic", fuel="Petrol", body="Hatchback", engine="2.0L Turbo", drive="FWD", colour="Tornado Red", features=["GTI sport seats", "Digital cockpit", "DCC suspension", "Rear camera"]),
    dict(make="Ford", model="Ranger Wildtrak", year=2021, price="46800000", mileage=44000, transmission="Automatic", fuel="Diesel", body="Pickup", engine="2.0L Bi-Turbo", drive="4WD", colour="Arctic White", features=["4WD selectable modes", "Roller shutter", "Touchscreen infotainment", "Tow bar"]),
    dict(make="Nissan", model="Pathfinder SV", year=2022, price="53500000", mileage=31000, transmission="Automatic", fuel="Petrol", body="SUV", engine="3.5L V6", drive="4WD", colour="Gun Metallic", features=["Three-row seating", "ProPILOT Assist", "Remote start", "Around-view monitor"]),
    dict(make="Mazda", model="CX-5 Grand Touring", year=2020, price="36200000", mileage=46000, transmission="Automatic", fuel="Petrol", body="SUV", engine="2.5L 4-Cylinder", drive="AWD", colour="Soul Red", features=["Bose audio", "Leather seats", "Head-up display", "Smart brake support"]),
    dict(make="Porsche", model="Macan S", year=2019, price="98500000", mileage=39000, transmission="Automatic", fuel="Petrol", body="SUV", engine="3.0L V6 Turbo", drive="AWD", colour="Carrara White", features=["Sport Chrono", "PASM", "Panoramic roof", "Premium audio"]),
    dict(make="Jeep", model="Grand Cherokee Limited", year=2021, price="58500000", mileage=37000, transmission="Automatic", fuel="Petrol", body="SUV", engine="3.6L V6", drive="4WD", colour="Diamond Black", features=["Selec-Terrain", "Leather upholstery", "Uconnect display", "Power liftgate"]),
    dict(make="Honda", model="CR-V EX-L", year=2022, price="42500000", mileage=29000, transmission="Automatic", fuel="Petrol", body="SUV", engine="1.5L Turbo", drive="AWD", colour="Platinum White", features=["Honda Sensing", "Power tailgate", "Leather seats", "Remote engine start"]),
    dict(make="Toyota", model="Hilux SR5", year=2020, price="49500000", mileage=63000, transmission="Automatic", fuel="Diesel", body="Pickup", engine="2.8L Turbo Diesel", drive="4WD", colour="Attitude Black", features=["4WD", "Rear differential lock", "Side steps", "Reverse camera"]),
]

# Unsplash image IDs for vehicle photography. Images are fetched at runtime
# and persisted into the database, not hotlinked by the website.
PHOTO_IDS = [
 "photo-1492144534655-ae79c964c9d7","photo-1503376780353-7e6692767b70","photo-1549317661-bd32c8ce0db2",
 "photo-1519641471654-76ce0107ad1b","photo-1552519507-da3b142c6e3d","photo-1533473359331-0135ef1b58bf",
 "photo-1503736334956-4c8f8e92946d","photo-1511919884226-fd3cad34687c","photo-1494976388531-d1058494cdd8",
 "photo-1542362567-b07e54358753","photo-1489824904134-891ab64532f1","photo-1504215680853-026ed2a45def",
 "photo-1553440569-bcc63803a83d","photo-1506610654-064fbba4780c","photo-1525609004556-c46c7d6cf023",
 "photo-1518306721680-3f4c0e1c8b9e","photo-1507136566006-cfc505b114fc","photo-1517524206127-48bbd363f3d7",
 "photo-1493238792000-8113da705763","photo-1485291571150-772bcfc10da5"
]

def _download_photo(photo_id):
    import urllib.request
    url = "https://images.unsplash.com/" + photo_id + "?auto=format&fit=crop&w=1400&q=82"
    req = urllib.request.Request(url, headers={"User-Agent": "CarWebsiteSampleSeeder/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = response.read(8 * 1024 * 1024 + 1)
        mime = response.headers.get_content_type()
    if len(data) > 8 * 1024 * 1024 or mime not in {"image/jpeg", "image/png", "image/webp"}:
        raise RuntimeError("Photo download returned an unsupported or oversized image: " + photo_id)
    return data, mime

def register_seed_command(app):
    @app.cli.command("seed-sample-vehicles")
    @click.option("--confirm", is_flag=True, help="Required confirmation for writing sample inventory.")
    def seed_sample_vehicles(confirm):
        if not confirm:
            raise click.ClickException("No changes made. Re-run with --confirm to add the sample inventory.")
        if not current_app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("postgresql"):
            raise click.ClickException("Sample inventory seeding is restricted to PostgreSQL.")
        inspector = inspect(db.engine)
        if not inspector.has_table("vehicle"):
            raise click.ClickException("Vehicle table is missing in the configured schema. Run init-db first.")
        existing = {v.slug for v in Vehicle.query.filter(Vehicle.slug.like("sample-%")).all()}
        added = 0
        images_added = 0
        try:
            for index, spec in enumerate(VEHICLES):
                name = spec["make"] + " " + spec["model"]
                slug = "sample-" + str(index + 1).zfill(2) + "-" + name.lower().replace(" ", "-")
                if slug in existing:
                    continue
                photo_id = PHOTO_IDS[index]
                photo, mime = _download_photo(photo_id)
                vehicle = Vehicle(
                    slug=slug, make=spec["make"], model=spec["model"], name=name,
                    year=spec["year"], price=Decimal(spec["price"]), currency="NGN",
                    mileage=spec["mileage"], mileage_unit="km",
                    transmission=spec["transmission"], fuel=spec["fuel"], condition="used",
                    body=spec["body"], engine=spec["engine"], drive=spec["drive"],
                    colour=spec["colour"],
                    description=(f'{spec["year"]} {name} in {spec["colour"]}. A sample listing with '
                                 f'{spec["mileage"]:,} km, {spec["engine"]}, {spec["transmission"].lower()} '
                                 f'transmission and {spec["drive"]} drive. Please confirm actual availability, '
                                 'condition and final price with the seller.'),
                    features_json=json.dumps(spec["features"]),
                    status="available", featured=(index < 4), published=True
                )
                db.session.add(vehicle)
                db.session.flush()
                # Store three distinct image files per vehicle. Same vehicle
                # photo source is cropped differently for gallery positions.
                for position, crop in enumerate(("entropy", "attention", "faces")):
                    url = (f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=1400&h=950&q=82&crop={crop}")
                    data, image_mime = _download_photo_url(url)
                    db.session.add(VehicleImage(
                        vehicle_id=vehicle.id,
                        filename=f"{slug}-{position+1}.jpg",
                        mime_type=image_mime, data=data, position=position
                    ))
                    images_added += 1
                added += 1
                db.session.flush()
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        click.echo(f"Created {added} sample vehicles and {images_added} image records. Existing listings were left unchanged.")

def _download_photo_url(url):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "CarWebsiteSampleSeeder/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = response.read(8 * 1024 * 1024 + 1)
        mime = response.headers.get_content_type()
    if len(data) > 8 * 1024 * 1024 or mime not in {"image/jpeg", "image/png", "image/webp"}:
        raise RuntimeError("Photo download returned an unsupported or oversized image.")
    return data, mime
