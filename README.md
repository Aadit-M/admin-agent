# AdminHelp

AdminHelp is an enterprise admin assistant with a React dashboard, FastAPI backend, and a LangGraph supervisor coordinating four specialist agents.

## Requirements

- Python 3.10+
- Node.js and npm

## Run locally in two terminals

From the project root, create and activate a virtual environment if you do not already have one, then install the Python packages:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create your local environment file from the example and add your Groq API key. Alternatively, enter the key in the dashboard **Settings**:

```powershell
Copy-Item .env.example .env
```

### Terminal 1 — FastAPI backend

From the project root, with the virtual environment activated:

```powershell
python -m uvicorn app:app --reload
```

### Terminal 2 — React frontend

From the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL printed in Terminal 2, usually `http://localhost:5173`. Vite proxies API requests to the FastAPI server at `http://127.0.0.1:8000`.

### Run the production build

To serve the built React app directly from FastAPI instead of using Vite, build the frontend and start the backend:

```powershell
cd frontend
npm install
npm run build
cd ..
python -m uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`.

Each browser workspace has isolated in-memory state. Restarting the backend clears sessions. Use **Settings → Reset workspace** to restore the seeded demo directory, purchase orders, and policies.
