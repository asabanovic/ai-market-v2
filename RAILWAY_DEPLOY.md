# Railway Deployment Guide

## Project Structure

This is a monorepo with two services:
- **backend** - Flask API (Python)
- **frontend** - Nuxt 3 (Node.js)

## Deployment Steps

### 1. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `ai-market-v2` repository

### 2. Create Services

You need to create **3 services**:

#### Service 1: PostgreSQL Database
- Click "New" → "Database" → "PostgreSQL"
- Railway auto-generates `DATABASE_URL`

#### Service 2: Backend (Flask)
- Click "New" → "GitHub Repo" → Select `ai-market-v2`
- Go to Settings → Set **Root Directory** to `/backend`
- Railway will auto-detect Python and use the config files

#### Service 3: Frontend (Nuxt)
- Click "New" → "GitHub Repo" → Select `ai-market-v2`
- Go to Settings → Set **Root Directory** to `/frontend`
- Railway will auto-detect Node.js and use the config files

### 3. Configure Environment Variables

#### Backend Variables (Required)
```
DATABASE_URL         → (auto-injected from PostgreSQL service)
SECRET_KEY           → (generate a secure random string)
FLASK_ENV            → production
BACKEND_URL          → https://your-backend.railway.app (REQUIRED for Google OAuth!)
OPENAI_API_KEY       → your-openai-key
ANTHROPIC_API_KEY    → your-anthropic-key
```

**IMPORTANT:** `BACKEND_URL` must be set correctly for Google OAuth to work!
- Production: `https://api.popust.ba`
- Staging: `https://backend-staging-a928.up.railway.app`

#### Backend Variables (Optional)
```
LANGSMITH_API_KEY    → for LangGraph tracing
SENDGRID_API_KEY     → for email notifications
AI_PIJACA_GOOGLE_CLIENT_ID     → for Google OAuth
AI_PIJACA_GOOGLE_CLIENT_SECRET → for Google OAuth
```

#### Frontend Variables (Required)
```
NUXT_PUBLIC_API_BASE           → https://your-backend.railway.app
NUXT_PUBLIC_GOOGLE_OAUTH_ENABLED → true/false
NODE_ENV                       → production
```

### 4. Link Services

1. In the backend service, click "Variables" → "Reference Variables"
2. Link `DATABASE_URL` from the PostgreSQL service
3. In the frontend service, link to backend URL

### 5. Database Migration

After first deployment, run migrations:
```bash
railway run -s backend alembic upgrade head
```

Or use Railway's shell:
1. Go to backend service → "Settings" → "Deploy"
2. Add one-time deploy command: `alembic upgrade head && gunicorn main:app...`

---

## Staging vs Production Deployment

### Option A: Separate Railway Projects (Recommended)

Create two Railway projects:
- `ai-market-staging` - for testing
- `ai-market-production` - for live

Use different GitHub branches:
- `develop` branch → deploys to staging
- `main` branch → deploys to production

### Option B: Railway Environments

Railway supports environments within a single project:
1. Go to Project Settings → Environments
2. Create "staging" and "production" environments
3. Each environment has its own variables and databases

### Branch-based Deployment Workflow

```
Feature Branch → PR to develop → Merge → Auto-deploy to Staging
                                ↓
              Test on Staging → PR to main → Merge → Auto-deploy to Production
```

Configure in Railway:
1. Backend service → Settings → "Build & Deploy"
2. Set "Branch" to `develop` for staging, `main` for production

---

## Custom Domain Setup

1. Go to service → Settings → "Networking" → "Custom Domain"
2. Add your domain (e.g., `api.aipijaca.com` for backend)
3. Add DNS CNAME record pointing to Railway's domain
4. Railway auto-provisions SSL

---

## Useful Commands

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to existing project
railway link

# Run commands in Railway environment
railway run -s backend python -c "print('hello')"

# View logs
railway logs -s backend

# Open shell
railway shell -s backend
```
