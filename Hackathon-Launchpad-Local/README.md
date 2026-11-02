# VaaniBuy - Local Setup

VaaniBuy is a local shopping-flow demo. Product search, approval-gated mock
orders, local SQLite history, and demo PDF receipts work. No real commerce
provider or payment is connected.

## Setup on Windows

1. Open CMD in this directory and run:

   setup.cmd

2. Add your Sarvam Model API key to `.env` for `test_sarvam.py`.
   `.env` is ignored by git; never commit or share it.

3. Add `SARVAM_API_KEY` to `.env` to enable the shopping assistant chat.
   The separate `SARVAM_AGENT_ID` and `SAMVAAD_API_KEY` are for Samvaad voice.
   Voice also requires the correct `SAMVAAD_ORG_ID` and
   `SAMVAAD_WORKSPACE_ID`. Keep both API keys server-side.

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

Open the local URL printed by Vite. Product results, order placement, and
payments are simulated; the explicit-approval flow never charges money.

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
