# Claude Development Instructions

## Local Development

**IMPORTANT: Use `./start.sh` for local development, NOT Docker Compose.**

The `start.sh` script runs the frontend with `npm run dev` which provides hot module reloading (HMR). Changes to frontend files will automatically refresh in the browser without rebuilding.

### Starting Development Environment

```bash
./start.sh
```

This will:
1. Start PostgreSQL with pgvector (Docker container)
2. Start the Flask backend (Python)
3. Start the Nuxt frontend with hot-reload (`npm run dev`)

### Stopping All Services

```bash
./stop.sh
```

### When to Use Docker Compose

Docker Compose (`docker-compose.yml`) is for **production-like testing only**:
- Testing the production build before deployment
- Testing Docker image builds
- CI/CD pipeline simulations

For development work, **always use `./start.sh`** to avoid slow rebuilds.

## Key URLs (Development)

- Frontend: http://localhost:3000
- Backend API: http://localhost:5001
- Database: localhost:5432 (postgres/devpass)

## Project Structure

- `frontend/` - Nuxt 3 application
- `backend/` - Flask API with PostgreSQL/pgvector
- `docker-compose.yml` - Production Docker setup
- `start.sh` / `stop.sh` - Development environment scripts

## Railway Deployment

- Staging: https://popust-ba-staging.up.railway.app
- Production: https://popust.ba

### Railway Service Names

- **Production backend**: `backend-prod`
- **Staging backend**: `backend`
- **Production frontend**: `frontend-prod`
- **Staging frontend**: `frontend`

### Running Migrations

Migrations use Alembic. Run from the `backend/` directory.

**Local development:**
```bash
cd backend
alembic upgrade head
```

**Production:**
```bash
cd backend
RAILWAY_ENVIRONMENT=production railway run --service backend-prod alembic upgrade head
```

**Staging:**
```bash
cd backend
RAILWAY_ENVIRONMENT=staging railway run --service backend alembic upgrade head
```

### Creating New Migrations

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Railway CLI Commands

**Check deployment status:**
```bash
railway status
```

**View logs:**
```bash
# Production
RAILWAY_ENVIRONMENT=production railway logs --service backend-prod

# Staging
RAILWAY_ENVIRONMENT=staging railway logs --service backend
```

**Redeploy service:**
```bash
# Production
RAILWAY_ENVIRONMENT=production railway redeploy --service backend-prod

# Staging
RAILWAY_ENVIRONMENT=staging railway redeploy --service backend
```

See `RAILWAY_DEPLOY.md` for more deployment instructions.

## UI/UX Rules

### Text Contrast - CRITICAL
**NEVER use light/white text on white or light backgrounds.** Always ensure sufficient contrast:
- On white/light backgrounds: use `text-gray-900`, `text-gray-800`, `text-gray-700`, or `text-gray-600`
- On dark backgrounds: use `text-white` or `text-gray-100`
- For secondary text on light backgrounds: use `text-gray-600` or `text-gray-500` (NOT text-gray-400 or lighter)
- For placeholders: `placeholder-gray-400` is acceptable

Examples:
- WRONG: `<span class="text-white">Text</span>` on a white card
- CORRECT: `<span class="text-gray-900">Text</span>` on a white card
