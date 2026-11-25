"""Idempotent demo inventory with openly licensed vehicle photography from Wikimedia Commons."""
import json
import re
from html import unescape
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from extensions import db
from models import Vehicle, VehicleImage

DISPLAY_MAKES = {"bmw": "BMW", "mercedes-benz": "Mercedes-Benz", "range rover": "Range Rover", "lexus": "Lexus", "audi": "Audi", "kia": "Kia"}

DEMO_CARS = [
    ("toyota","Camry",2024,44500000,"Sedan","2.5L Hybrid","Pearl White",18000),
    ("toyota","Corolla",2023,28500000,"Sedan","1.8L Petrol","Silver Metallic",22000),
    ("toyota","RAV4",2024,52000000,"SUV","2.5L Hybrid","Magnetic Grey",12000),
    ("toyota","Land Cruiser",2023,185000000,"SUV","3.5L V6 Twin Turbo","Black",16000),
    ("toyota","Hilux",2024,68000000,"Pickup","2.8L Diesel","White",9000),
    ("lexus","ES 350",2023,68500000,"Sedan","3.5L V6","Sonic Titanium",21000),
    ("lexus","RX 350",2024,112000000,"SUV","2.4L Turbo","Caviar Black",11000),
    ("lexus","LX 600",2023,235000000,"SUV","3.5L V6 Twin Turbo","Graphite Black",14000),
    ("lexus","IS 350 F Sport",2022,62500000,"Sedan","3.5L V6","Infrared",28000),
    ("lexus","NX 350",2024,82500000,"SUV","2.4L Turbo","Atomic Silver",8000),
    ("mercedes-benz","C-Class C300",2023,79500000,"Sedan","2.0L Turbo","Obsidian Black",19000),
    ("mercedes-benz","E-Class E350",2022,86500000,"Sedan","2.0L Turbo","Polar White",26000),
    ("mercedes-benz","S-Class S500",2023,220000000,"Sedan","3.0L Inline-6","Diamond White",12000),
    ("mercedes-benz","GLC 300",2024,98500000,"SUV","2.0L Turbo","Selenite Grey",9000),
    ("mercedes-benz","GLE 450",2023,145000000,"SUV","3.0L Turbo Hybrid","Black",15000),
    ("bmw","330i",2023,68500000,"Sedan","2.0L Turbo","Portimao Blue",17000),
    ("bmw","530i",2022,73500000,"Sedan","2.0L Turbo","Alpine White",24000),
    ("bmw","740i",2023,185000000,"Sedan","3.0L Turbo","Carbon Black",13000),
    ("bmw","X3 xDrive30i",2024,92500000,"SUV","2.0L Turbo","Brooklyn Grey",10000),
    ("bmw","X5 xDrive40i",2023,138000000,"SUV","3.0L Turbo","Phytonic Blue",16000),
    ("audi","A4",2023,58500000,"Sedan","2.0L TFSI","Mythos Black",18000),
    ("audi","A6",2022,73500000,"Sedan","2.0L TFSI","Glacier White",25000),
    ("audi","Q5",2024,89500000,"SUV","2.0L TFSI","Daytona Grey",9000),
    ("audi","Q7",2023,132000000,"SUV","3.0L TFSI","Navarra Blue",15000),
    ("audi","e-tron",2023,118000000,"SUV","Electric","Chronos Grey",7000),
    ("honda","Accord",2023,38500000,"Sedan","1.5L Turbo","Platinum White",23000),
    ("honda","Civic",2024,32500000,"Sedan","2.0L Petrol","Crystal Black",10000),
    ("honda","CR-V",2023,49500000,"SUV","1.5L Turbo","Lunar Silver",19000),
    ("honda","Pilot",2022,58500000,"SUV","3.5L V6","Modern Steel",27000),
    ("nissan","Altima",2023,33500000,"Sedan","2.5L Petrol","Gun Metallic",21000),
    ("nissan","Patrol",2022,128000000,"SUV","5.6L V8","White Pearl",30000),
    ("nissan","X-Trail",2024,46500000,"SUV","2.5L Petrol","Diamond Black",8000),
    ("hyundai","Sonata",2023,34500000,"Sedan","2.5L Petrol","Hampton Grey",17000),
    ("hyundai","Tucson",2024,48500000,"SUV","2.5L Petrol","Amazon Grey",9000),
    ("hyundai","Santa Fe",2023,62500000,"SUV","2.5L Turbo","Creamy White",14000),
    ("kia","K5",2023,36500000,"Sedan","2.5L Petrol","Wolf Grey",16000),
    ("kia","Sportage",2024,48500000,"SUV","2.5L Petrol","Jungle Green",8500),
    ("kia","Sorento",2023,62500000,"SUV","2.5L Turbo","Everlasting Silver",14000),
    ("ford","Mustang GT",2022,98500000,"Coupe","5.0L V8","Race Red",18000),
    ("ford","Explorer",2023,78500000,"SUV","2.3L EcoBoost","Agate Black",16000),
    ("ford","Ranger",2024,62500000,"Pickup","2.0L Bi-Turbo Diesel","Arctic White",7000),
    ("volkswagen","Golf GTI",2023,48500000,"Hatchback","2.0L TSI","Kings Red",12000),
    ("volkswagen","Tiguan",2024,58500000,"SUV","2.0L TSI","Deep Black",9000),
    ("volkswagen","Passat",2022,38500000,"Sedan","2.0L TSI","Reflex Silver",26000),
    ("porsche","Cayenne",2023,195000000,"SUV","3.0L V6 Turbo","Carrara White",11000),
    ("porsche","911 Carrera",2022,245000000,"Coupe","3.0L Twin Turbo","Guards Red",9000),
    ("range rover","Sport",2023,245000000,"SUV","3.0L Inline-6","Santorini Black",12000),
    ("range rover","Evoque",2024,112000000,"SUV","2.0L Turbo","Firenze Red",6000),
    ("mazda","CX-5",2024,42500000,"SUV","2.5L Petrol","Soul Red",8000),
    ("mazda","Mazda 6",2022,33500000,"Sedan","2.5L Petrol","Machine Grey",23000),
]

def _commons_images(make, model):
    """Fetch three distinct, angle-oriented Commons images; fail closed if unavailable."""
    from urllib.error import URLError
    search_name = f"{make} {model}"
    found = []
    used = set()
    for angle in ("front view", "side view", "rear view"):
        params = urlencode({
            "action": "query", "generator": "search",
            "gsrsearch": f'filetype:bitmap "{search_name}" car {angle}',
            "gsrnamespace": 6, "gsrlimit": 8,
            "prop": "imageinfo", "iiprop": "url|extmetadata",
            "iiurlwidth": 1400, "format": "json"
        })
        request = Request(
            "https://commons.wikimedia.org/w/api.php?" + params,
            headers={"User-Agent": "PremierMotorworksDemoSeeder/1.0 (vehicle catalogue demo)"}
        )
        try:
            with urlopen(request, timeout=25) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, ValueError) as exc:
            raise RuntimeError(f"Could not retrieve demo photos for {search_name}: {exc}") from exc
        pages = payload.get("query", {}).get("pages", {})
        candidates = sorted(pages.values(), key=lambda page: page.get("title", ""))
        selected = next((page for page in candidates if page.get("imageinfo") and page["imageinfo"][0].get("thumburl") not in used), None)
        if not selected:
            continue
        info = selected["imageinfo"][0]
        url = info.get("thumburl") or info.get("url")
        if not url or url in used:
            continue
        image_request = Request(url, headers={"User-Agent": "PremierMotorworksDemoSeeder/1.0"})
        with urlopen(image_request, timeout=35) as response:
            data = response.read(12 * 1024 * 1024 + 1)
            mime = response.headers.get_content_type()
        if len(data) > 12 * 1024 * 1024 or mime not in {"image/jpeg", "image/png", "image/webp"}:
            continue
        used.add(url)
        title = re.sub(r"[^A-Za-z0-9._-]+", "-", selected.get("title", "vehicle-photo"))[-220:]
        metadata = info.get("extmetadata", {})
        artist = re.sub(r"<[^>]+>", "", unescape(metadata.get("Artist", {}).get("value", "Unknown author"))).strip()
        license_name = metadata.get("LicenseShortName", {}).get("value", "license not stated")
        license_url = metadata.get("LicenseUrl", {}).get("value", "")
        credit = f"{title} — {artist}, {license_name} {license_url}".strip()
        found.append((data, mime, title, angle, credit))
        time.sleep(0.15)
    if len(found) != 3:
        raise RuntimeError(
            f"Only {len(found)} of 3 angle photos were found for {search_name}. "
            "No vehicles were added; retry the seed command later."
        )
    return found

def add_demo_inventory():
    """Add missing demo vehicles without changing existing or previously added inventory."""
    added = 0
    image_count = 0
    for make, model, year, price, body, engine, colour, mileage in DEMO_CARS:
        slug = re.sub(r"[^a-z0-9]+", "-", f"demo-{make}-{model}-{year}".lower()).strip("-")
        if Vehicle.query.filter_by(slug=slug).first():
            continue
        photos = _commons_images(make, model)
        display_make = DISPLAY_MAKES.get(make.lower(), make.title())
        credits = "\\n".join(f"Photo {index + 1}: {photo[4]}" for index, photo in enumerate(photos))
        vehicle = Vehicle(
            slug=slug, make=display_make, model=model,
            name=f"{display_make} {model}", year=year, price=price,
            currency="NGN", mileage=mileage, mileage_unit="km",
            transmission="Automatic", fuel="Petrol", condition="used",
            body=body, engine=engine, drive="All-wheel drive" if body == "SUV" else "Front-wheel drive",
            colour=colour,
            description="DEMO LISTING — Sample vehicle added for catalogue preview only. Specifications, price and availability are illustrative, not a real offer.\\n\\nPHOTO CREDITS (Wikimedia Commons):\\n" + credits,
            features_json=json.dumps(["Demo listing", "Illustrative specifications", "Sample catalogue vehicle"]),
            status="available", featured=False, published=True
        )
        db.session.add(vehicle)
        db.session.flush()
        for position, (data, mime, filename, angle, credit) in enumerate(photos):
            db.session.add(VehicleImage(
                vehicle_id=vehicle.id, filename=f"{angle.replace(' ', '-')}-{filename}",
                mime_type=mime, data=data, position=position
            ))
            image_count += 1
        added += 1
    db.session.commit()
    return added, image_count
