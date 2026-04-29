# AIATS

AIATS is split into a Python Flask backend and a TypeScript React frontend.

## Structure

```text
backend/   Flask API, ML pipeline, resume parsing, roadmap JSON data
frontend/  Vite + React + TypeScript user interface
docs/      Project, frontend, API, database, and user-flow documentation
```

## Backend

```powershell
cd backend
pip install -r requirements.txt
python main.py
```

The Flask backend runs on:

```text
http://localhost:5000
```

Important APIs:

- `GET /api/health`
- `GET /api/track/github/<username>`
- `GET /api/track/leetcode/<username>`
- `GET /api/track/codeforces/<username>`
- `POST /api/ats-analyze`
- `GET /api/roadmaps`
- `GET /api/roadmaps/<slug>`

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

The Vite frontend runs on:

```text
http://localhost:5173
```

During development, Vite proxies `/api` to Flask on port `5000`.

## Production Build

```powershell
cd frontend
npm run build
```

After build, Flask can serve the compiled TypeScript frontend from `frontend/dist`.
