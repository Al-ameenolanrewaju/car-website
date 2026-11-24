# Premier Motorworks — Vehicle Marketplace

A responsive automotive catalogue with a Flask backend and a private administration workspace. The storefront keeps the warm, dark editorial visual language from the reference design while vehicle data, enquiries, settings and uploaded photographs are managed server-side.

## Stack
- Python 3.11+ / Flask
- Flask-SQLAlchemy + Flask-Migrate
- PostgreSQL in production; SQLite for local development
- Flask-Login password-hash authentication
- Flask-WTF CSRF protection
- Flask-Limiter for login and public enquiry rate limits
- Vanilla JavaScript storefront

## Customer website
- Responsive homepage and vehicle catalogue
- Database-backed inventory, search and filters
- Dedicated vehicle detail view with gallery and specifications
- Guest saved-car shortlist (stored in that browser)
- Enquiry form that saves leads to the database
- WhatsApp enquiry link uses the number configured in Admin Settings

## Admin workspace
Open /admin/login.
- Overview dashboard: total, available, reserved and sold inventory; total and new enquiries; team count and recent administrative activity
- Secure admin sign-in and sign-out
- Administrator-only team management: create staff accounts, assign administrator/manager roles, and activate or deactivate access; the last active administrator cannot be removed
- Add, edit, publish/unpublish and delete vehicle listings
- Upload multiple vehicle photographs; images are stored as database binary data, not on the web server filesystem
- Vehicle status: available, reserved or sold
- Featured vehicle toggle
- Customer enquiry inbox with new/contacted/closed workflow and email/WhatsApp follow-up links
- Business name, email, WhatsApp number, address and currency settings
- Audit records for vehicle and settings changes

## Local setup
1. Install Python 3.11 or newer.
2. Create and activate a virtual environment.
3. Install dependencies: pip install -r requirements.txt
4. Copy .env.example to .env, then set a long random SECRET_KEY. Keep COOKIE_SECURE=false for local HTTP development. Flask CLI loads this file through python-dotenv.
5. Create the database tables: flask --app app init-db
6. Create your first administrator: flask --app app create-admin
7. Start the development server: flask --app app run

Visit http://127.0.0.1:5000 and sign in at http://127.0.0.1:5000/admin/login.

The optional flask --app app seed-demo command inserts three unpublished sample listings. Review and replace these with real inventory before publishing.

## Production deployment
Use a managed PostgreSQL database (Render Postgres, Supabase, or another PostgreSQL provider). Configure these environment variables in the hosting dashboard:
- SECRET_KEY: long, randomly generated secret; never commit it
- DATABASE_URL: PostgreSQL connection string
- COOKIE_SECURE=true
- RATELIMIT_STORAGE_URI: Redis URL for shared rate-limit state when running multiple instances (the default in-memory store is suitable only for a single instance)
- ADMIN_EMAIL / ADMIN_PASSWORD are not needed when using the interactive create-admin command

Build command: pip install -r requirements.txt
Start command: flask --app app init-db && gunicorn app:app

After the first deploy, open a one-off shell and run flask --app app create-admin. Do not put a default admin password in source code or a public environment file.

For future schema changes, initialize Flask-Migrate once with flask --app app db init, create reviewed migrations with flask --app app db migrate -m "describe change", then apply with flask --app app db upgrade. Migrations should be additive and must not drop existing customer or inventory data.

## Storage and operational notes
- Vehicle records, business settings, enquiries and uploaded image bytes live in the configured database.
- No local upload folder or persistent web-server disk is required.
- Guest saved cars currently use browser local storage. Cross-device saved lists require customer accounts and are not represented as a server-side account feature.
- The demo listings are unpublished and must not be treated as real inventory.
- Configure and verify the correct business WhatsApp number before launch.
- Production should use HTTPS, a managed database with backups, a strong secret key, and a shared Redis rate-limit store for multiple app instances.
- Add an email provider and operational notification policy if automatic email alerts are required; the current enquiry workflow stores and displays enquiries in Admin.

## Tests
Run python -m unittest discover -s tests -v.
The test suite covers storefront responses, database inventory reads, enquiry persistence, admin authentication and unpublished listing visibility.
