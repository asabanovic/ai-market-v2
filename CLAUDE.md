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

See `RAILWAY_DEPLOY.md` for deployment instructions.
