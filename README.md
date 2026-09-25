# Smart Tatkal Assistant

A compliant railway booking-assistance web app. It helps users save passenger details,
prepare a booking plan, view a Tatkal countdown, and track PNRs. It does NOT automate
IRCTC login, CAPTCHA/OTP, payment, or ticket booking.

## Stack
- Python 3.10+
- Flask
- SQLite
- HTML/CSS/JavaScript
- SQLAlchemy

## Run
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Demo availability
The app uses sample train/availability data in `seed.py`. Replace the service layer
with an authorized railway data/API integration if you obtain one. Do not scrape,
bypass CAPTCHA/OTP, or automate IRCTC booking.

## Demo credentials
Register a user from the login page.


## Authorized railway API integration

This project now includes `services/railway_provider.py`.

### Demo mode
Default:
```text
RAILWAY_PROVIDER=demo
```
The app uses the included sample train data.

### Authorized mode
If you have an actual railway/IRCTC-authorized web-service contract, set:
```text
RAILWAY_PROVIDER=authorized
RAILWAY_API_BASE_URL=https://your-authorized-provider.example/api
RAILWAY_API_TOKEN=YOUR_PROVIDER_TOKEN
```

The adapter expects:
- `GET /trains?from=...&to=...&date=...&quota=Tatkal`
- `GET /pnr/<10-digit-pnr>`

The exact endpoint paths and authentication scheme must be changed to match
the documentation supplied by your authorized provider. No fake IRCTC endpoint
is included.

### Why this is structured this way
IRCTC's published policy describes Web Services APIs for Principal Service
Providers (PSPs), and distinguishes PSP/RSP commercial e-ticketing channels.
The project therefore uses a provider adapter instead of pretending that a
public IRCTC API exists.

Do not enter personal IRCTC passwords, CAPTCHA answers, OTPs, payment
credentials, or session cookies into this app. Do not scrape IRCTC pages or
automate an unauthorized account.


## Turning this into an authorized commercial service

The project now has:
- `services/commercial_service.py`
- `commercial_config.example.json`
- `/commercial` compliance page

Production path:

1. Obtain the appropriate IRCTC PSP/RSP authorization through the applicable
   IRCTC process/contract.
2. Obtain the official technical integration/API documentation and credentials
   from the contracted PSP/IRCTC.
3. Replace the demo provider configuration with the documented endpoints.
4. Map the provider's official fare, availability, booking, cancellation and
   PNR response schemas.
5. Configure only the service charges permitted by the agreement.
6. Keep customer IRCTC passwords, OTPs, CAPTCHA values, session cookies and
   payment credentials out of this application's database.
7. Complete privacy, security, logging, refund and customer-support controls
   before production.

The application cannot make a business "authorized" merely by changing a
configuration value.
