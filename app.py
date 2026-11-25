import os
import click
from flask import Flask, abort, jsonify, send_file, send_from_directory
from config import Config
from extensions import db, migrate, login_manager, csrf, limiter

def create_app(config_object=Config):
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(config_object)
    os.makedirs(app.instance_path, exist_ok=True)
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
        return send_from_directory(app.root_path, "index.html")

    @app.get("/collection")
    def collection_page():
        return send_from_directory(app.root_path, "collection.html")

    @app.get("/car.html")
    def car_page():
        return send_from_directory(app.root_path, "car.html")

    @app.get("/saved-cars.html")
    def saved_page():
        return send_from_directory(app.root_path, "saved-cars.html")

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
        if len(password) < 1:
            raise click.ClickException("Use an admin password of at least 1 character.")
        user = AdminUser(email=email, name=name.strip() or "Administrator")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo("Administrator account created.")

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        # Optional first-admin bootstrap for hosted environments. The account is
        # created once; later restarts never overwrite an existing password.
        admin_email = app.config.get("ADMIN_EMAIL", "").strip().lower()
        admin_password = app.config.get("ADMIN_PASSWORD", "")
        if admin_email and admin_password:
            existing_admin = AdminUser.query.filter_by(email=admin_email).first()
            if existing_admin is None:
                if len(admin_password) < 1:
                    raise click.ClickException("ADMIN_PASSWORD must contain at least 1 character.")
                admin = AdminUser(email=admin_email, name="Administrator", role="admin", active=True)
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()
                click.echo("Initial administrator account created from environment configuration.")
            else:
                click.echo("Configured administrator already exists; password was not changed.")
        click.echo("Database tables created. Use flask db migrate/upgrade for production schema changes.")


    @app.context_processor
    def inject_globals():
        from flask_wtf.csrf import generate_csrf
        return {"csrf_token": generate_csrf}

    return app

app = create_app()
