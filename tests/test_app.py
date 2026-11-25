import os
import unittest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-car-marketplace")
from app import create_app
from extensions import db
from models import AdminUser, Vehicle, VehicleImage, Enquiry

class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False

class MarketplaceTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        admin = AdminUser(email="admin@example.test", name="Test Admin")
        admin.set_password("correct-horse-battery-staple")
        db.session.add(admin)
        self.vehicle = Vehicle(
            slug="toyota-camry-2022", make="Toyota", model="Camry",
            name="Toyota Camry", year=2022, price=25000000, currency="NGN",
            mileage=25000, mileage_unit="km", transmission="Automatic",
            fuel="Petrol", condition="used", body="Sedan",
            status="available", published=True
        )
        db.session.add(self.vehicle)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_health_endpoint_checks_database(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok", "database": "ok"})

    def test_health_endpoint_returns_503_when_database_check_fails(self):
        with patch("public.db.session.execute", side_effect=SQLAlchemyError("database unavailable")):
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {"status": "error", "database": "unavailable"})

    def test_storefront_and_public_inventory(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/static/script.js", response.data)
        response.close()
        data = self.client.get("/api/vehicles").get_json()
        self.assertEqual(len(data["vehicles"]), 1)
        self.assertEqual(data["vehicles"][0]["id"], "toyota-camry-2022")

    def test_public_enquiry_is_saved(self):
        response = self.client.post("/api/enquiries", json={
            "name": "Ada Customer", "email": "ada@example.test",
            "phone": "+2348012345678", "message": "Is this car available?",
            "vehicle_id": "toyota-camry-2022"
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Enquiry.query.count(), 1)
        self.assertEqual(Enquiry.query.first().vehicle_id, self.vehicle.id)

    def test_multi_vehicle_enquiry_is_saved_as_one_lead(self):
        second = Vehicle(
            slug="honda-accord-2023", make="Honda", model="Accord",
            name="Honda Accord", year=2023, price=30000000, currency="NGN",
            mileage=18000, mileage_unit="km", transmission="Automatic",
            fuel="Petrol", condition="used", body="Sedan",
            status="available", published=True
        )
        db.session.add(second)
        db.session.commit()
        response = self.client.post("/api/enquiries", json={
            "name": "Ada Customer", "email": "ada@example.test",
            "phone": "+2348012345678", "message": "Please contact me about both cars.",
            "vehicle_ids": ["toyota-camry-2022", "honda-accord-2023"]
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["vehicle_count"], 2)
        enquiry = Enquiry.query.one()
        self.assertEqual({car.slug for car in enquiry.selected_vehicles},
                         {"toyota-camry-2022", "honda-accord-2023"})
        self.assertEqual(enquiry.vehicle.slug, "toyota-camry-2022")

    def test_multi_vehicle_enquiry_rejects_unavailable_vehicle(self):
        self.vehicle.status = "sold"
        db.session.commit()
        response = self.client.post("/api/enquiries", json={
            "name": "Ada Customer", "email": "ada@example.test",
            "phone": "+2348012345678", "message": "I want these cars.",
            "vehicle_ids": ["toyota-camry-2022"]
        })
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Enquiry.query.count(), 0)

    def test_multi_vehicle_enquiry_rejects_duplicate_vehicle_ids(self):
        response = self.client.post("/api/enquiries", json={
            "name": "Ada Customer", "email": "ada@example.test",
            "phone": "+2348012345678", "message": "I want this car twice.",
            "vehicle_ids": ["toyota-camry-2022", "toyota-camry-2022"]
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Enquiry.query.count(), 0)

    def test_admin_login_and_dashboard(self):
        response = self.client.post("/admin/login", data={
            "email": "admin@example.test",
            "password": "correct-horse-battery-staple"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Toyota Camry", response.data)

    def test_admin_can_create_and_publish_vehicle(self):
        self.client.post("/admin/login", data={"email": "admin@example.test", "password": "correct-horse-battery-staple"})
        response = self.client.post("/admin/vehicles/new", data={"name": "Honda Civic Sport", "make": "Honda", "model": "Civic", "year": "2023", "price": "32000000", "currency": "NGN", "mileage": "12000", "mileage_unit": "km", "transmission": "Automatic", "fuel": "Petrol", "condition": "used", "body": "Sedan", "status": "available", "published": "on"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        created = Vehicle.query.filter_by(name="Honda Civic Sport").first()
        self.assertIsNotNone(created)
        self.assertTrue(created.published)
        public_ids = [item["id"] for item in self.client.get("/api/vehicles").get_json()["vehicles"]]
        self.assertIn(created.slug, public_ids)

    def test_admin_can_save_business_settings(self):
        self.client.post("/admin/login", data={"email": "admin@example.test", "password": "correct-horse-battery-staple"})
        response = self.client.post("/admin/settings", data={"business_name": "Example Motors", "contact_email": "sales@example.test", "whatsapp_number": "2348012345678", "currency": "NGN", "address": "Lagos, Nigeria"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        settings = self.client.get("/api/site-settings").get_json()
        self.assertEqual(settings["business_name"], "Example Motors")
        self.assertEqual(settings["whatsapp_number"], "2348012345678")

    def test_admin_can_save_social_media_urls(self):
        self.client.post("/admin/login", data={"email": "admin@example.test", "password": "correct-horse-battery-staple"})
        response = self.client.post("/admin/settings", data={
            "business_name": "Example Motors",
            "instagram_url": "https://instagram.com/examplemotors",
            "facebook_url": "https://facebook.com/examplemotors",
            "tiktok_url": "https://tiktok.com/@examplemotors",
            "x_url": "https://x.com/examplemotors",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        settings = self.client.get("/api/site-settings").get_json()
        self.assertEqual(settings["instagram_url"], "https://instagram.com/examplemotors")
        self.assertEqual(settings["facebook_url"], "https://facebook.com/examplemotors")
        self.assertEqual(settings["tiktok_url"], "https://tiktok.com/@examplemotors")
        self.assertEqual(settings["x_url"], "https://x.com/examplemotors")

    def test_admin_rejects_social_media_urls_without_http_scheme(self):
        self.client.post("/admin/login", data={"email": "admin@example.test", "password": "correct-horse-battery-staple"})
        response = self.client.post("/admin/settings", data={
            "business_name": "Example Motors", "instagram_url": "javascript:alert(1)"
        })
        self.assertEqual(response.status_code, 400)
        settings = self.client.get("/api/site-settings").get_json()
        self.assertEqual(settings["instagram_url"], "")

    def test_init_db_bootstraps_admin_with_any_non_empty_password(self):
        self.app.config["ADMIN_EMAIL"] = "single-char@example.test"
        self.app.config["ADMIN_PASSWORD"] = "x"
        result = self.app.test_cli_runner().invoke(args=["init-db"])
        self.assertEqual(result.exit_code, 0, f"{result.output} {result.exception!r}")
        admin = AdminUser.query.filter_by(email="single-char@example.test").one()
        self.assertTrue(admin.check_password("x"))

    def test_admin_can_manage_vehicle_categories(self):
        self.client.post("/admin/login", data={"email": "admin@example.test", "password": "correct-horse-battery-staple"})
        added = self.client.post("/admin/categories", data={"action": "add", "name": "Electric SUV"}, follow_redirects=True)
        self.assertEqual(added.status_code, 200)
        self.assertIn(b"Electric SUV", added.data)
        renamed = self.client.post("/admin/categories", data={"action": "rename", "old_name": "Sedan", "name": "Saloon"}, follow_redirects=True)
        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(db.session.get(Vehicle, self.vehicle.id).body, "Saloon")
        blocked = self.client.post("/admin/categories", data={"action": "delete", "old_name": "Saloon"}, follow_redirects=True)
        self.assertEqual(blocked.status_code, 200)
        self.assertEqual(db.session.get(Vehicle, self.vehicle.id).body, "Saloon")

    def test_admin_can_manage_vehicle_brands(self):
        self.client.post("/admin/login", data={"email": "admin@example.test", "password": "correct-horse-battery-staple"})
        added = self.client.post("/admin/brands", data={"action": "add", "name": "Lexus"}, follow_redirects=True)
        self.assertEqual(added.status_code, 200)
        self.assertIn(b"Lexus", added.data)
        renamed = self.client.post("/admin/brands", data={"action": "rename", "old_name": "Toyota", "name": "Toyota Motor"}, follow_redirects=True)
        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(db.session.get(Vehicle, self.vehicle.id).make, "Toyota Motor")

    def test_admin_can_create_team_account(self):
        self.client.post("/admin/login", data={"email": "admin@example.test", "password": "correct-horse-battery-staple"})
        response = self.client.post("/admin/team", data={"action": "create", "name": "Sales Manager", "email": "sales@example.test", "password": "a-strong-temporary-password", "role": "manager"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        member = AdminUser.query.filter_by(email="sales@example.test").first()
        self.assertIsNotNone(member)
        self.assertEqual(member.role, "manager")
        self.assertTrue(member.check_password("a-strong-temporary-password"))

    def test_wrong_admin_password_is_rejected(self):
        self.client.post("/admin/login", data={
            "email": "admin@example.test", "password": "wrong-password"
        })
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_private_inventory_is_not_public(self):
        self.vehicle.published = False
        db.session.commit()
        self.assertEqual(self.client.get("/api/vehicles").get_json()["vehicles"], [])


    def test_seed_demo_adds_50_vehicles_with_three_photos_each_idempotently(self):
        photos = [
            (b"demo-front", "image/jpeg", "front-demo.jpg", "front view", "Front photo credit"),
            (b"demo-side", "image/jpeg", "side-demo.jpg", "side view", "Side photo credit"),
            (b"demo-rear", "image/jpeg", "rear-demo.jpg", "rear view", "Rear photo credit"),
        ]
        with patch("demo_inventory._commons_images", return_value=photos):
            result = self.app.test_cli_runner().invoke(args=["seed-demo"])
            self.assertEqual(result.exit_code, 0, result.output)
            demo_vehicles = Vehicle.query.filter(Vehicle.slug.like("demo-%")).all()
            self.assertEqual(len(demo_vehicles), 50)
            self.assertEqual(VehicleImage.query.count(), 150)
            self.assertTrue(all(vehicle.published for vehicle in demo_vehicles))
            self.assertTrue(all(len(vehicle.images) == 3 for vehicle in demo_vehicles))
            second = self.app.test_cli_runner().invoke(args=["seed-demo"])
            self.assertEqual(second.exit_code, 0, second.output)
            self.assertEqual(Vehicle.query.filter(Vehicle.slug.like("demo-%")).count(), 50)
            self.assertEqual(VehicleImage.query.count(), 150)
            self.assertEqual(Vehicle.query.filter_by(slug="toyota-camry-2022").count(), 1)

if __name__ == "__main__":
    unittest.main()
