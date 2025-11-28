# Railway Deployment Guide

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

| Branch | Purpose | Railway Environment |
|--------|---------|---------------------|
| `main` | Production code | production |
| `develop` | Development code | staging |

## Deploying to Railway

### Option 1: Git Push (Automatic)
```bash
# Deploy to production (main branch)
git push origin main

# Deploy to staging (develop branch)
git push origin develop
```

### Option 2: Railway CLI (Manual)

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

## URLs

| Environment | Frontend | API |
|-------------|----------|-----|
| Production | https://popust.ba | https://api.popust.ba |
| Staging | https://frontend-*.up.railway.app | https://backend-*.up.railway.app |
