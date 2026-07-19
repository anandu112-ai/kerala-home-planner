# 🏡 Kerala Home Planner

A full-stack construction cost planning application for Kerala homes, featuring a beautiful modern UI and machine learning predictions.

## 📁 Project Structure

This project is a monorepo consisting of:
*   **Frontend (`/`)**: A fast, premium, search-optimized **TanStack Start** (React + Router + Nitro) application.
*   **Backend (`/backend`)**: A **FastAPI** (Python) service that loads and runs a trained Machine Learning model to calculate precise construction estimates and recommendations.

---

## 🚀 Local Development

### 1. Running the Frontend
Make sure you are in the root directory:
```bash
npm install
npm run dev
```
The frontend will start on [http://localhost:5173](http://localhost:5173).

### 2. Running the Backend
Navigate to the `backend` directory:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
The backend API will run on [http://localhost:8000](http://localhost:8000). You can access the automatic documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 🚆 Deployment to Railway

This project is configured to run out-of-the-box on **Railway**. Because it is a monorepo, you will deploy **two separate services** from the same GitHub repository.

### 1. Deploy the Frontend
1. Create a new service on Railway connected to your GitHub repository.
2. Under the service's **Settings**:
    *   **Root Directory**: Leave empty or set to `/`.
    *   **Build Command**: Railway will automatically build using `npm run build` (configured to build as a Node.js server).
    *   **Start Command**: Railway will automatically run the built server via `npm start` (`node .output/server/index.mjs`).
3. Under the service's **Variables**, add:
    *   `BACKEND_URL`: Set to your backend's public URL (e.g., `https://kerala-home-planner-backend.up.railway.app`).
4. Generate a public domain under **Public Networking** to get your frontend URL.

### 2. Deploy the Backend
1. Create a second service in the same Railway project connected to the same GitHub repository.
2. Rename this service to `kerala-home-planner-backend`.
3. Under the service's **Settings**:
    *   **Root Directory**: Set this to `backend`. *(Crucial: This scopes the builder to the backend folder)*.
4. Under the service's **Variables**, add:
    *   `ENVIRONMENT`: `production`
    *   `FRONTEND_URL`: Set this to your public frontend URL (e.g., `https://kerala-home-planner.up.railway.app`) to enable CORS access.
5. Railway's Nixpacks builder will automatically detect Python, install dependencies from `requirements.txt`, and start uvicorn using the `Procfile`.

### 3. Connect Frontend → Backend
After deploying the backend service, copy its public domain URL and set it as an environment variable in the **frontend** service on Railway:
*   `BACKEND_URL`: Set to your backend's public URL (e.g., `https://kerala-home-planner-backend.up.railway.app`).

> [!NOTE]
> If `BACKEND_URL` is not set, the frontend server-side function will default to `http://127.0.0.1:8000`, which works for local development. If the backend is unreachable, the app gracefully falls back to the built-in client-side estimate and shows a notification to the user.
