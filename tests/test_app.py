import os
import unittest
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-car-marketplace")
from app import create_app
from extensions import db
from models import AdminUser, Vehicle, Enquiry

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

    def test_storefront_and_public_inventory(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/static/script.js", response.data)
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

    def test_admin_login_and_dashboard(self):
        response = self.client.post("/admin/login", data={
            "email": "admin@example.test",
            "password": "correct-horse-battery-staple"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Toyota Camry", response.data)

    def test_wrong_admin_password_is_rejected(self):
        self.client.post("/admin/login", data={
            "email": "admin@example.test", "password": "wrong-password"
        })
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_private_inventory_is_not_public(self):
        self.vehicle.published = False
        db.session.commit()
        self.assertEqual(self.client.get("/api/vehicles").get_json()["vehicles"], [])

if __name__ == "__main__":
    unittest.main()
