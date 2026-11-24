import os
import click
from flask import Flask, abort, jsonify, send_file, send_from_directory
from config import Config
from extensions import db, migrate, login_manager, csrf, limiter

def create_app(config_object=Config):
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(config_object)
    if not app.config.get("SECRET_KEY"):
        if app.config.get("TESTING"):
            app.config["SECRET_KEY"] = "test-only-secret"
        else:
            raise RuntimeError("Set SECRET_KEY in the environment before starting the application.")
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "admin.login"
    login_manager.login_message_category = "info"
    csrf.init_app(app)
    limiter.init_app(app)

    from models import AdminUser, Vehicle, VehicleImage, Enquiry, SiteSetting
    from public import public_bp
    from admin import admin_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    @app.get("/")
    def home():
        return send_from_directory(".", "index.html")

    @app.get("/car.html")
    def car_page():
        return send_from_directory(".", "car.html")

    @app.get("/saved-cars.html")
    def saved_page():
        return send_from_directory(".", "saved-cars.html")

    @app.get("/api/csrf-token")
    def csrf_token_api():
        from flask_wtf.csrf import generate_csrf
        return jsonify({"csrf_token": generate_csrf()})

    @app.get("/media/<int:image_id>")
    def vehicle_media(image_id):
        image = db.session.get(VehicleImage, image_id)
        if not image:
            abort(404)
        from io import BytesIO
        response = send_file(BytesIO(image.data), mimetype=image.mime_type, download_name=image.filename, max_age=86400)
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.option("--name", prompt="Administrator name", default="Administrator")
    @click.password_option()
    def create_admin(email, name, password):
        email = email.strip().lower()
        if AdminUser.query.filter_by(email=email).first():
            raise click.ClickException("An administrator with that email already exists.")
        if len(password) < 12:
            raise click.ClickException("Use an admin password of at least 12 characters.")
        user = AdminUser(email=email, name=name.strip() or "Administrator")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo("Administrator account created.")

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        click.echo("Database tables created. Use flask db migrate/upgrade for production schema changes.")

    @app.cli.command("seed-demo")
    def seed_demo():
        import json
        if Vehicle.query.first():
            click.echo("Inventory already exists; no demo records were added.")
            return
        demo = [
            dict(slug="bmw-330i-m-sport",make="BMW",model="3 Series",name="BMW 330i M Sport",year=2024,price=58900000,currency="NGN",mileage=12400,mileage_unit="km",transmission="Automatic",fuel="Petrol",condition="used",body="Sedan",engine="2.0L Turbo",drive="Rear-wheel drive",colour="Portimao Blue",description="A beautifully balanced sports sedan with a driver-focused cabin and confident performance.",features=["M Sport package","Leather upholstery","Panoramic roof","Parking sensors","Apple CarPlay"],published=False),
            dict(slug="mercedes-c300",make="Mercedes-Benz",model="C-Class",name="Mercedes-Benz C 300",year=2025,price=64900000,currency="NGN",mileage=0,mileage_unit="km",transmission="Automatic",fuel="Petrol",condition="new",body="Sedan",engine="2.0L Turbo",drive="Rear-wheel drive",colour="Obsidian Black",description="Modern luxury with an elegant interior and responsive turbocharged performance.",features=["MBUX infotainment","Digital display","Heated seats","Driver assistance"],published=False),
            dict(slug="audi-q5-premium",make="Audi",model="Q5",name="Audi Q5 Premium Plus",year=2024,price=52750000,currency="NGN",mileage=8200,mileage_unit="km",transmission="Automatic",fuel="Petrol",condition="used",body="SUV",engine="2.0L TFSI",drive="Quattro all-wheel drive",colour="Daytona Grey",description="A versatile premium SUV with composed road manners and a beautifully finished cabin.",features=["Quattro AWD","Virtual cockpit","Panoramic sunroof","360 camera"],published=False)
        ]
        for item in demo:
            item["features_json"] = json.dumps(item.pop("features"))
            db.session.add(Vehicle(**item))
        db.session.commit()
        click.echo("Three unpublished demo vehicles added. Review and publish them in Admin.")

    @app.context_processor
    def inject_globals():
        from flask_wtf.csrf import generate_csrf
        return {"csrf_token": generate_csrf}

    return app

app = create_app()
