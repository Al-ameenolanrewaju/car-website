# Redesign and backend implementation notes

## Repository boundary
All implementation work is in this repository. The clothing catalogue repository was inspected only as a visual reference and is not modified by this project.

## Design reference
The storefront uses the reference site's warm near-black palette, ivory typography, muted neutrals, restrained gold accents, serif editorial headings, framed imagery, generous spacing, and responsive card/grid layout. Vehicle terminology, specifications, search filters, galleries and enquiry actions are adapted to the automotive context.

## Architecture discovery
The target repository originally contained only static HTML, CSS and vanilla JavaScript. There was no backend, database, authentication layer, admin dashboard, or API to preserve. This branch therefore adds a Flask application and database models rather than pretending the original static files already had server-side functionality.

## Backend and persistence
- Flask application factory and PostgreSQL/SQLite configuration
- SQLAlchemy models for administrator accounts, vehicles, vehicle images, enquiries, site settings and audit logs
- Password-hash authentication, protected admin routes, CSRF protection and login/enquiry rate limits
- Public JSON API for published vehicle inventory, site contact settings and customer enquiries
- Database binary storage for vehicle photos; no local uploads directory or persistent web-server disk
- CLI commands for initial schema creation, first administrator creation and optional unpublished demo listings

## Admin workspace
- Dashboard summary cards for inventory status, enquiries and team accounts
- Recent administrative activity panel
- Vehicle CRUD, publication/featured controls, image upload/removal and available/reserved/sold states
- Enquiry inbox with new/contacted/closed workflow
- Business settings for name, email, WhatsApp, address and currency
- Administrator-only team account creation and role/active-state management

## Customer experience
- Database-backed inventory on the storefront and detail pages
- Search and combined client-side filters
- Guest saved list in browser storage; customer accounts and cross-device saved lists are not part of this release
- Customer vehicle enquiries are stored in the database and displayed in Admin
- WhatsApp contact uses the number set in Admin Settings

## Safety and release boundaries
- Three optional demo vehicles are inserted as unpublished records; they are not genuine stock and do not appear publicly until an administrator reviews and publishes them.
- No default admin credentials are committed. The first administrator must be created with the Flask CLI.
- No real business WhatsApp number or email provider has been supplied/configured.
- A managed PostgreSQL database, secret key, HTTPS hosting and initial administrator account are required for deployment.
- Automated tests and JavaScript syntax checks run in GitHub Actions. A live browser/device QA and real deployment check are still required before production.
