# Premier Motorworks

A responsive automotive catalogue inspired by the visual system and shopping experience of the clothing-website reference repository.

## Current architecture

This repository is a static HTML, CSS and vanilla JavaScript website. It does not currently contain a Flask/Django/Node backend, database, API, authentication, admin dashboard or server-side enquiry endpoint. The redesign preserves that architecture rather than silently introducing a replacement backend.

## Pages

- `index.html` — homepage, vehicle search, combined filters, brand shortcuts and inventory.
- `car.html?id=<vehicle-id>` — dedicated vehicle details, three-image gallery, specifications, features and enquiry form.
- `saved-cars.html` — saved vehicle shortlist.

## Functionality

- Search by keyword, make, model and year.
- Combined price, mileage, transmission, fuel, condition and body-type filters.
- New/pre-owned condition tabs and brand shortcuts.
- Save/remove favourites with browser `localStorage` persistence for guests.
- Vehicle detail pages with image gallery and specification grid.
- WhatsApp enquiry message preparation. The WhatsApp share flow opens without assuming a seller phone number; the user chooses the destination chat.
- Responsive desktop, tablet and mobile layouts, lazy-loaded listing/gallery imagery, reduced-motion support and accessible control labels.

## Vehicle data

The current inventory is demonstration data defined in the `cars` array near the top of `script.js`. Replace it with verified inventory before production. Each record includes its own image URLs, price, mileage, specifications, condition, body type, description and features.

## Production requirements not present in this repository

The following cannot be delivered securely with a static frontend alone:

- Authenticated saved cars synchronised across devices.
- Seller/admin accounts and inventory management.
- Database-backed vehicle records and image management.
- Server-side enquiry storage, email delivery or seller routing.
- Server-side validation, rate limiting and audit logs.

Those features require a backend/API and a database. They have deliberately not been simulated as if local browser storage were a secure server.

## Local preview

Open `index.html` in a browser or serve this folder with any static HTTP server. Vehicle detail links use `car.html?id=<vehicle-id>`.

## Validation

The JavaScript file was syntax-checked after implementation. A live browser/device test and end-to-end backend integration test remain outstanding because this repository has no backend and the current connected GitHub workflow does not provide a browser preview session.
