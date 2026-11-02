# VaaniBuy

VaaniBuy is a local demo shopping assistant and mock commerce workflow built for a hackathon-style prototype. It combines a FastAPI backend, a React frontend, and Sarvam AI integration to let users:

- search demo products
- ask for shopping assistance in chat
- generate an itemized proposal
- require explicit approval before creating a simulated order
- download a demo PDF receipt.
- check local voice configuration without exposing secrets

This repository contains the full project under the `Hackathon-Launchpad-Local` folder.

## What this project does

VaaniBuy is intentionally a safe demo environment. It does not connect to a real payment gateway or a real commerce provider. The app simulates:

- product search and catalog browsing
- AI shopping chat using Sarvam
- budget-aware proposal creation
- explicit approval before order placement
- local SQLite persistence for proposals, orders, and receipts
- receipt generation with a clearly labeled demo PDF

## Tech stack

- Backend: Python, FastAPI, SQLite
- Frontend: React + Vite
- AI: Sarvam AI APIs
- PDF generation: ReportLab
- Testing: pytest

## Repository structure

```text
VAANIBUY/
├── README.md
├── Hackathon-Launchpad-Local/
│   ├── .env.example
│   ├── .gitignore
│   ├── API-INTEGRATIONS.md
│   ├── README.md
│   ├── requirements.txt
│   ├── run.cmd
│   ├── setup.cmd
│   ├── test_sarvam.py
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── utils/
│   │   └── main.py
│   ├── config/
│   ├── skills/
│   ├── tests/
│   ├── web/
│   └── workflows/
└──
```

## Quick start

From the repository root:

```bash
cd Hackathon-Launchpad-Local
```

Create your environment file from the example:

```bash
copy .env.example .env
```

Then set the required keys in `.env`:

```dotenv
SARVAM_API_KEY=
SARVAM_AGENT_ID=
SAMVAAD_API_KEY=
SAMVAAD_ORG_ID=
SAMVAAD_WORKSPACE_ID=
```

Install Python dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On Windows, you can also run the helper script:

```cmd
setup.cmd
```

## Run the backend

```cmd
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Run the frontend

Open a second terminal and run:

```bash
cd web
npm install
npm run dev
```

Then open the local URL shown by Vite in your browser.

## Demo API overview

The backend exposes a few local shopping endpoints:

- `GET /api/products?q=rice` — search demo products
- `POST /api/chat` — ask the Sarvam shopping assistant
- `POST /api/proposals` — create an itemized shopping proposal
- `POST /api/proposals/{id}/approve` — requires explicit approval before placement
- `GET /api/orders` — view demo orders
- `GET /api/orders/{id}` — view a specific order
- `GET /api/orders/{id}/receipt` — download a demo PDF receipt
- `GET /api/voice/status` — check whether voice-related configuration is present

## Important notes

- `.env` is local-only and must not be committed.
- No real payment is processed in this demo.
- The app stores data locally in SQLite and is intended for local testing and demos.
- The project is designed to showcase shopping workflows, approval gating, and AI-assisted assistance without production commerce integrations.

## Documentation

For more details, see:

- `Hackathon-Launchpad-Local/README.md`
- `Hackathon-Launchpad-Local/API-INTEGRATIONS.md`

## License

This project does not currently declare a repository license.

