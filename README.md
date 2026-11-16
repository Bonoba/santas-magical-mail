# Santa's Magical Mail — working Flask starter

## Run locally

Install Python 3.10+ and run:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. The **sample PDF** works immediately. Checkout requires Stripe configuration.

## Activate real payments

1. Create a Stripe account and complete its identity/business verification.
2. Set environment variables `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and `PUBLIC_BASE_URL` (see `.env.example`). Never publish secret keys.
3. Deploy to a Python-compatible HTTPS host with persistent storage for `orders.sqlite3`. Start command: `gunicorn app:app`.
4. In Stripe Dashboard add a webhook endpoint at `https://YOUR_DOMAIN/stripe-webhook` and subscribe to `checkout.session.completed`; copy its signing secret into `STRIPE_WEBHOOK_SECRET`.
5. Test with Stripe test keys and a test card; check that paid orders download and unpaid orders do not. Then switch to live keys after verification.
6. Add your business email, privacy policy, refund policy, terms, and customer support details before accepting real orders. Set up receipts or transactional email through a provider; currently the buyer downloads on the confirmation page, not via email.

## Important launch notes

- This is a runnable **starter**, not a fully hosted production business. You must supply accounts, hosting, domain, and keys. Hosting, processing, and advertising may incur costs.
- PDF delivery is immediate after verified payment. No postal fulfillment, email automation, admin dashboard, taxes, or refunds automation are implemented.
- The address field is stored but **not printed** on the PDF; it is optional and unnecessary for digital delivery. Remove it if you do not offer mailed letters.
- Children’s data: obtain details from adults, collect the minimum needed, publish a privacy policy, and implement retention/deletion controls. Consult legal guidance on COPPA and applicable privacy laws before launch.
- SQLite needs a persistent volume and is appropriate for modest traffic; for national scale migrate to hosted PostgreSQL, use a secure object store, rate limits, backups, email receipts, and monitoring.
- Ensure a domain name and product branding do not infringe third-party trademarks.
- Use `gunicorn app:app` behind HTTPS. Do not use Flask debug mode on a public server.

## National marketing launch checklist

1. Create a landing page with example (watermarked) PDFs and clear pricing.
2. Publish SEO pages such as "personalized Santa letter printable", "letter from Santa PDF", and "Santa letter for siblings".
3. Share short original videos showing the printable result on Pinterest, Instagram Reels, and TikTok, aimed at adults.
4. Offer a parent referral coupon and a 3-letter family bundle after implementing coupon logic.
5. Partner with parent newsletters, local holiday fairs, and family bloggers. Never directly target children with marketing or collect data from children.
6. Measure conversion, refunds, customer support response time, and ad acquisition cost before spending on national ads.
