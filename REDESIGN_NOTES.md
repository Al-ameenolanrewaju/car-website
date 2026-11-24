# Design and architecture review

## Repository findings

### Reference: clothing-website

The reference is a Flask/Jinja catalogue application. Its storefront is composed from reusable navigation, footer and product-card templates, with dedicated home, collection, product-detail and wishlist views. Its visual system uses a deep warm brown/black base, ivory text, muted warm neutrals, gold accents, serif editorial headings, generous spacing, framed hero/product imagery and thin warm borders. Its storefront JavaScript supports persistent guest cart/wishlist state, image gallery selection, drawers, filtering, and cached partial navigation.

### Target: car-website (before this branch)

The target contained only three files: `index.html`, `styles.css` and `script.js`. It was a static single-page demonstration with three hard-coded vehicle cards, basic make/model/year/price/condition filtering and a mobile menu. There was no server-side architecture to preserve: no database, authentication, API, admin panel, backend routes or migrations.

## Feature mapping

| Clothing reference | Automotive implementation |
|---|---|
| Store header/navigation | Sticky Premier Motorworks navigation |
| Editorial hero | Two-column automotive hero with framed vehicle image |
| Collection/product grid | Vehicle inventory cards |
| Product category/variant filters | Make, model, year, price, mileage, transmission, fuel, condition and body filters |
| Product detail page/gallery | Dedicated `car.html` detail page with image gallery and vehicle specifications |
| Wishlist/save for later | Saved cars page backed by browser localStorage |
| WhatsApp product order | WhatsApp vehicle enquiry message |
| Collection/brand links | Automotive brand shortcuts |
| Store footer/editorial band | Automotive editorial section and matching footer |

## Implementation boundary

The target remains a static website. Guest favourites persist in the current browser via localStorage. Authenticated/cross-device favourites, database-backed listings and server-side lead management are not claimed or emulated. A backend must be designed as a separate, explicit phase once the desired server stack and deployment are confirmed.

## Review and validation status

- Repository trees inspected before code changes.
- Target changes isolated to `redesign/clothing-reference`.
- JavaScript syntax validation passed after implementation.
- Visual browser testing, mobile device testing, live WhatsApp destination testing and production data verification remain outstanding.
