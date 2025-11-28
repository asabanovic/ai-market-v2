# Railway Deployment Guide

## Development Workflow

> **IMPORTANT**: All development work happens on the `develop` branch. The `main` branch is for production-ready code only.

### Git Flow

```
develop (default working branch) → staging environment
    ↓ (merge when tested)
main (production-ready) → production environment
```

### Daily Development

```bash
# Always work on develop
git checkout develop

# Make changes, commit
git add .
git commit -m "Your changes"

# Push to trigger staging deployment
git push origin develop

# Test on staging: https://frontend-*.up.railway.app
```

### Deploy to Production

```bash
# After testing on staging, merge to main
git checkout main
git merge develop
git push origin main

# Production auto-deploys to popust.ba
```

### Quick Reference

| Action | Command |
|--------|---------|
| Start working | `git checkout develop` |
| Deploy to staging | `git push origin develop` |
| Deploy to production | `git checkout main && git merge develop && git push origin main` |
| Sync develop with main | `git checkout develop && git merge main && git push origin develop` |

---

## Project Structure

The Railway project `popust.ba` has **two separate environments**:

### Production Environment
| Service | Domain | Purpose |
|---------|--------|---------|
| `backend-prod` | api.popust.ba | Production API |
| `frontend-prod` | popust.ba | Production frontend |
| `pgvector-IKy1` | N/A | PostgreSQL database with pgvector |

### Staging Environment
| Service | Domain | Purpose |
|---------|--------|---------|
| `backend` | *.railway.app | Staging API |
| `frontend` | *.railway.app | Staging frontend |
| `pgvector` | N/A | Staging PostgreSQL database |

## Git Branches

| Branch | Purpose | Railway Environment | Auto-Deploy |
|--------|---------|---------------------|-------------|
| `develop` | **Default working branch** | staging | Yes |
| `main` | Production releases only | production | Yes |

## Deploying to Railway

### Automatic Deployment (Preferred)

Railway auto-deploys when you push to GitHub:

```bash
# Deploy to staging (daily work)
git push origin develop

# Deploy to production (after testing)
git checkout main
git merge develop
git push origin main
```

### Manual CLI Deployment (Emergency/Debug)

**Deploy to Production:**
```bash
# Link to production environment first
railway link -e production

# Deploy backend
cd backend
railway up --service backend-prod

# Deploy frontend
cd frontend
railway up --service frontend-prod
```

**Deploy to Staging:**
```bash
# Link to staging environment first
railway link -e staging

# Deploy backend
cd backend
railway up --service backend

# Deploy frontend
cd frontend
railway up --service frontend
```

## Environment Variables

### Backend Production (`backend-prod`)
Key variables (full list in Railway dashboard):
- `DATABASE_URL` - Uses Railway reference: `${{pgvector-IKy1.DATABASE_URL}}`
- `FLASK_ENV=production`
- `CORS_ORIGINS=https://popust.ba,https://frontend-prod-production.up.railway.app`
- `BACKEND_URL=https://api.popust.ba`
- `OPENAI_API_KEY` - For AI features
- `INFOBIP_*` - For SMS/Email notifications
- `AWS_*` - For S3 file storage
- `LANGSMITH_*` - For LLM tracing

### Frontend Production (`frontend-prod`)
- `NUXT_PUBLIC_API_URL=https://api.popust.ba`
- `NODE_ENV=production`
- `HOST=0.0.0.0`

### Staging Environment Variables
Staging should mirror production variables but with staging-specific values:
- `DATABASE_URL=${{pgvector.DATABASE_URL}}` (staging database)
- `FLASK_ENV=staging`
- `CORS_ORIGINS=https://frontend-*.up.railway.app`

## Database Connection

To show the visual connection line between services in Railway dashboard, use Railway reference syntax:
```
DATABASE_URL=${{pgvector-IKy1.DATABASE_URL}}
```

This ensures Railway knows the services are connected and displays the dotted line.

## Database Initialization

The backend Dockerfile handles database setup automatically:
1. Runs `init_db_schema.py` to create base SQLAlchemy tables
2. Checks if Alembic is at head, stamps if needed
3. Runs `alembic upgrade head` for any new migrations
4. Starts gunicorn server

## Database Migrations

```bash
# Create a new migration (run locally)
cd backend
alembic revision --autogenerate -m "Description of changes"

# Migrations auto-run on deploy via Dockerfile
# To manually run:
alembic upgrade head
```

## Troubleshooting

### Check Service Status
```bash
railway status
railway service status --all
```

### View Logs
```bash
# Production logs
railway logs --service backend-prod
railway logs --service frontend-prod

# Staging logs
railway logs --service backend
railway logs --service frontend
```

### Check Variables
```bash
railway variables --service backend-prod
railway variables --service frontend-prod
```

### Set Variables
```bash
railway variables --set "KEY=value" --service backend-prod
```

### Switch Environments
```bash
# Switch to production
railway link -e production

# Switch to staging
railway link -e staging
```

## URLs

| Environment | Frontend | API |
|-------------|----------|-----|
| Production | https://popust.ba | https://api.popust.ba |
| Staging | https://frontend-*.up.railway.app | https://backend-*.up.railway.app |
| Local | http://localhost:3000 | http://localhost:5001 |

## Local Development

```bash
# Start local development servers
./start.sh

# Or manually:
cd backend && python main.py &
cd frontend && npm run dev &
```

## CI/CD Notes

- **Staging**: Auto-deploys on push to `develop` branch
- **Production**: Auto-deploys on push to `main` branch
- **Database migrations**: Run automatically on container startup
- **Build caching**: Railway caches Docker layers for faster builds

## For Claude Code

When making code changes:
1. Always work on the `develop` branch
2. Test locally first with `./start.sh`
3. Push to `develop` to deploy to staging
4. Only merge to `main` after staging verification
5. Never commit directly to `main`
