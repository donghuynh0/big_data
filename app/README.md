# Parking System Frontend

This directory contains the Nuxt 4 frontend for the Parking System dashboard. It displays real-time parking status and vehicle details, consuming data via WebSocket and REST from a backend service running at `http://localhost:8000`.

## Prerequisites

- Node.js `>=18`
- A package manager: `pnpm` (recommended), `npm`, or `yarn`
- For backend (optional but recommended): Python `>=3.10`

## Install Dependencies

From this `app/` folder:

```bash
pnpm install
# or
npm install
# or
yarn install
```

## Run Frontend (Development)

Start the Nuxt dev server on `http://localhost:3000`:

```bash
pnpm dev
# or
npm run dev
# or
yarn dev
```

Routes:

- `/` Dashboard view with zones and spots
- `/car/:license_plate` Vehicle detail page

The frontend expects a backend at `http://localhost:8000` for:

- Socket.IO: `ws://localhost:8000`
- REST: `http://localhost:8000/api/data` and `http://localhost:8000/api/vehicle/:plate`

## Start Backend (WebSocket + REST)

The backend lives in `../parking_system`. Start it to feed real-time data:

```bash
cd ../parking_system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python web_server.py
```

Notes:

- The server listens on `http://localhost:8000` (host `0.0.0.0`).
- Kafka settings are defined in `web_server.py` (`KAFKA_SERVER`, `KAFKA_TOPIC`). Adjust to your environment.
- Optional: generate events with `parking_producer.py` after configuring Kafka.

## Production Build

Build the app:

```bash
pnpm build
# or
npm run build
# or
yarn build
```

Preview the production build locally:

```bash
pnpm preview
# or
npm run preview
# or
yarn preview
```

## Troubleshooting

- WebSocket not connecting: ensure the backend is running on `http://localhost:8000`.
- Different backend host/port: update hardcoded endpoints in:
  - `app/app/components/DashboardSparking.vue`
  - `app/app/pages/car/[id].vue`
- CORS issues: backend enables CORS by default (`flask-cors`). Check browser console for errors.
- Kafka not available: the UI still loads but with empty/zero stats.

## Reference

- Nuxt docs: https://nuxt.com/docs/getting-started/introduction
