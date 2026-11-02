# VaaniBuy - Local Setup

VaaniBuy is a local shopping-flow demo. Product search, approval-gated mock
orders, local SQLite history, and demo PDF receipts work. No real commerce
provider or payment is connected.

## Setup on Windows

1. Open CMD in this directory and run:

   setup.cmd

2. Add `SARVAM_API_KEY` to `.env` to enable the chat, voice assistant, and
   `test_sarvam.py`. `.env` is ignored by git; never commit or share it. The voice
   turn uses Saaras speech-to-text, Sarvam chat, and Bulbul text-to-speech;
   the key stays on the backend. The separate `SARVAM_AGENT_ID`,
   `SAMVAAD_API_KEY`, `SAMVAAD_ORG_ID`, and `SAMVAAD_WORKSPACE_ID` are for
   managed Samvaad agent sessions.

## Run the backend

```cmd
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/health

## Run the web app

In another terminal:

```cmd
cd web
npm install
npm run dev
```

Open the local URL printed by Vite. Allow microphone access and tap **Talk**;
recordings are limited to 25 seconds. Browser voice requires localhost or
HTTPS. Product results, order placement, and payments are simulated; the
explicit-approval flow never charges money.

## Deploy on Vercel

The repository-root `vercel.json` configures the `api` service for FastAPI and
the `web` service for Vite. `/api/*` and `/health` route to the API; all other
paths route to the web app. Set `SARVAM_API_KEY` in the Vercel API service's
environment variables. The browser uses same-origin API paths, so no service
binding is needed. Vercel stores the demo SQLite database under `/tmp`, which
is writable but ephemeral; use a hosted database before relying on persistent
orders.

## Local API

- `GET /api/products?q=rice` — search demo products.
- `POST /api/chat` — Sarvam shopping assistant; requires `SARVAM_API_KEY`.
- `POST /api/proposals` — create an itemized proposal from product IDs.
- `POST /api/proposals/{id}/approve` — requires explicit approval; creates one
  idempotent demo order and a `simulated_not_charged` payment record.
- `GET /api/orders` and `GET /api/orders/{id}` — demo order history/details.
- `GET /api/orders/{id}/receipt` — download a clearly labeled demo PDF.
- `GET /api/voice/status` — reports configuration booleans only; never returns
  credentials.

For the API modules and remaining real-provider integrations, see
[API integrations](./API-INTEGRATIONS.md).

## Verify the Model API key

After adding `SARVAM_API_KEY`, run `run.cmd`. This makes a real Sarvam API
request using `sarvam-105b-conversations`.

## Sarvam references

- [Voice Agents quickstart](https://docs.sarvam.ai/voice-agents/quickstart)
- [Deploy with code](https://docs.sarvam.ai/voice-agents/deploy/deploy-with-code)
- [API tools for backend integrations](https://docs.sarvam.ai/voice-agents/build/tools/https-tool)
