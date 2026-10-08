# Implementation Plan: Hostinger Deployment Compatibility

## Objective
Enable seamless deployment of the Autonomous RFx Intelligence Engine on Hostinger across all hosting tiers (Docker / VPS / Cloud / Git Web App / Passenger WSGI).

## Identified Problem
The Hostinger deployment on `qgenerator.elimenots.xyz` completed the Git sync from repository `qgenerator`, but the web server returned **403 Forbidden** because:
1. Standard web servers (Nginx/LiteSpeed/Apache on Hostinger) look for an entry point (`index.html`, `index.php`, `.htaccess`, or container `Dockerfile`) and reject directory browsing by default.
2. Streamlit apps require a running Python runtime listening on an assigned port (`PORT` / `8501` / `8080` / `80`) with `0.0.0.0` binding, disabled CORS/XSRF for external reverse proxies, and websocket support.
3. Lack of deployment artifacts (`Dockerfile`, `.dockerignore`, `docker-compose.yml`, `.streamlit/config.toml`, `start.sh`, `Procfile`, `.htaccess`, `passenger_wsgi.py`).

## Proposed Architecture & Files

### 1. Docker & Container Support
- **`Dockerfile`**: Lightweight Python 3.11-slim container with build tools, dependencies, healthcheck, and dynamic `$PORT` support.
- **`docker-compose.yml`**: Compose specification with port mappings (`8501:8501`, `80:8501`), restart policies, and environment file linking.
- **`.dockerignore`**: Exclude unnecessary files (`.git`, `.venv`, `artifacts/`, `vendor_dataset/archive/`, `__pycache__`).

### 2. Streamlit Production Configuration
- **`.streamlit/config.toml`**: Configure production server settings (`headless = true`, `address = "0.0.0.0"`, `enableCORS = false`, `enableXsrfProtection = false`, `maxUploadSize = 200`).

### 3. Process & Startup Scripts
- **`start.sh`**: Production startup script that reads `$PORT` (default 8501/80) and starts Streamlit with appropriate flags.
- **`Procfile`**: Standard process definition (`web: ./start.sh` or `streamlit run app.py`).

### 4. Hostinger Web / Reverse Proxy / Passenger Fallbacks
- **`.htaccess`**: Apache/LiteSpeed reverse proxy and rewrite configuration to forward web traffic to localhost:8501 with WebSocket support (`ws://`).
- **`passenger_wsgi.py`**: WSGI bridge script for Hostinger Cloud/cPanel Python App manager.
- **`index.php` / `index.html`**: Zero-configuration smart fallback that redirects or proxies to the active Streamlit instance to eliminate 403 Forbidden errors.

### 5. Documentation
- Update `README.md`, `architecture.md`, and `AI_context.md` with step-by-step Hostinger deployment instructions (Docker, VPS, and Shared/Cloud Python App).

## Verification Plan
1. Validate tests pass locally.
2. Verify all deployment configs syntax and permission execution.
3. Document Hostinger deployment setup guide.
