# VaaniBuy API and integration files

## Implemented local API

| API | Status | Implementation |
|---|---|---|
| Demo product search | Working; sample catalog only | `app/api/routes.py`, `app/services/catalog.py` |
| Sarvam shopping chat | Working when `SARVAM_API_KEY` is configured | `app/api/routes.py` |
| Browser voice turn (Saaras transcription → Sarvam reply → Bulbul speech) | Working when `SARVAM_API_KEY` is configured | `app/api/routes.py`, `web/src/main.jsx` |
| Itemized purchase proposal | Working; server recalculates prices and validates budget | `app/api/routes.py` |
| Customer approval and order | Working; approval required, idempotent, simulated | `app/api/routes.py`, `app/services/store.py` |
| Order history/details | Working; local SQLite | `app/api/routes.py`, `app/services/store.py` |
| PDF receipt | Working; explicitly marked as a demo, not an invoice | `app/api/routes.py` |
| Voice setup status | Working; returns only configured/not-configured flags | `app/api/routes.py` |

`app/main.py` mounts the API and initializes the local database. SQLite data is
stored in the ignored `data/` directory. No real order or charge is made.

`POST /api/voice/turn` accepts multipart audio, conversation history, and a
language code; it returns the transcript, assistant reply, and WAV audio.
Recordings are limited to 10 MB in the API and 25 seconds in the browser.
Sarvam Model API credentials stay server-side. This is separate from the
managed Samvaad voice-agent SDK, which still needs valid app, organization, and
workspace IDs and a server-side session/auth flow.

## Provider API modules needed before real launch

These are integration files/contracts to add after selecting and receiving
authorized provider credentials; the demo intentionally does not pretend they
exist.

| File to add | External API / purpose | Required before |
|---|---|---|
| `app/services/samvaad.py` | Sarvam Voice Agents session SDK and server-side session creation. Needs `SAMVAAD_API_KEY`, agent/app ID, organization ID, and workspace ID. | Live voice conversations |
| `app/api/voice.py` | Backend session endpoint or short-lived session-token proxy; never send a long-lived API key to the browser. | Connecting the web microphone |
| `app/services/commerce.py` | Authorized ONDC network participant or seller-specific commerce APIs for live catalog, inventory, delivery quotes, and order placement. | Real product search and fulfillment |
| `app/services/payment.py` | Selected payment gateway's order/checkout API; store provider transaction IDs only. | Real customer charges |
| `app/api/webhooks.py` | Verified, idempotent payment and seller callbacks (signature verification before state changes). | Payment/order status callbacks |
| `app/services/tracking.py` | Selected seller/logistics tracking API and normalized delivery states. | Live order tracking |
| `app/services/identity.py` | Authentication/session provider, customer identity, saved addresses, and consent. | Multi-user production |
| `app/services/receipt.py` | Replace demo receipt with merchant invoices and lawful tax receipt data. | Real purchase receipts |

Do not enable real checkout until the payment and commerce integrations support
server-side verification, idempotency, audit logging, and reconciliation. Never
allow an agent tool to place an order without a fresh, explicit customer
approval bound to the exact proposal total and items.
