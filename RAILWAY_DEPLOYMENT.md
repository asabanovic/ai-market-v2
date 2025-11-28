# Railway Deployment Guide

This guide explains how to deploy AI Market V2 to Railway for both staging and production environments.

## Architecture

The application consists of 3 services:
- **Backend**: Flask API (Python)
- **Frontend**: Nuxt 3 SSR (Node.js)
- **Database**: PostgreSQL with pgvector extension

## Prerequisites

1. Railway account (https://railway.app)
2. GitHub repository connected to Railway
3. AWS S3 bucket for file uploads (bucket: `aipijaca`)

## Creating a New Railway Project

### Step 1: Create Project

```bash
# Login to Railway CLI
railway login

# Create new project
railway init
```

Or via Railway Dashboard:
1. Go to https://railway.app/new
2. Select "Deploy from GitHub repo"
3. Choose your repository

### Step 2: Add PostgreSQL Database

1. In Railway dashboard, click "+ New"
2. Select "Database" > "PostgreSQL"
3. The `DATABASE_URL` will be automatically available to services

### Step 3: Configure Backend Service

1. Click "+ New" > "GitHub Repo"
2. Select your repo and configure:
   - **Root Directory**: `backend`
   - **Branch**: `main` (production) or `develop` (staging)

#### Backend Environment Variables

Set these in Railway Dashboard > Backend Service > Variables:

```bash
# Database (auto-set by Railway if using their PostgreSQL)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Security
SESSION_SECRET=<generate-secure-random-string>
JWT_SECRET=<generate-secure-random-string>
ADMIN_PASSWORD=<your-admin-password>

# CORS - Frontend URL (set after frontend is deployed)
CORS_ORIGINS=https://your-frontend-url.up.railway.app
BACKEND_URL=https://your-backend-url.up.railway.app

# AWS S3 for file uploads
AWS_ACCESS_KEY_ID=<your-aws-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret>
AWS_REGION=eu-central-1
AWS_S3_BUCKET=aipijaca

# OpenAI
OPENAI_API_KEY=<your-openai-key>

# Infobip SMS (optional)
INFOBIP_API_KEY=<your-infobip-key>
INFOBIP_BASE_URL=<your-infobip-url>
INFOBIP_SENDER=<your-sender-id>

# Credits Configuration
ADMIN_WEEKLY_CREDITS=100000
REGULAR_USER_WEEKLY_CREDITS=10

# LangSmith Tracing (optional)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-langsmith-key>
LANGSMITH_PROJECT=ai-market-production

# Flask
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

### Step 4: Configure Frontend Service

1. Click "+ New" > "GitHub Repo"
2. Select your repo and configure:
   - **Root Directory**: `frontend`
   - **Branch**: `main` (production) or `develop` (staging)

#### Frontend Environment Variables

```bash
# API URL - Backend URL
NUXT_PUBLIC_API_URL=https://your-backend-url.up.railway.app

# Node
NODE_ENV=production
HOST=0.0.0.0
```

### Step 5: Generate Domains

For each service (backend and frontend):
1. Go to Service > Settings > Networking
2. Click "Generate Domain" to get a `.up.railway.app` domain
3. Or add a custom domain

### Step 6: Update CORS After Deployment

After both services are deployed:
1. Go to Backend > Variables
2. Update `CORS_ORIGINS` with the actual frontend URL
3. Update `BACKEND_URL` with the actual backend URL
4. Redeploy backend

## Environment-Specific Configuration

### Staging (develop branch)
- Uses `develop` branch
- Separate Railway project recommended
- Can use same S3 bucket with different prefix

### Production (main branch)
- Uses `main` branch
- Separate Railway project
- Consider dedicated S3 bucket or prefix

## Service Configuration Files

### Backend (`backend/railway.toml`)
```toml
[deploy]
healthcheckPath = "/api/health"
healthcheckTimeout = 100
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[env]
FLASK_ENV = "production"
PYTHONUNBUFFERED = "1"
```

### Frontend (`frontend/railway.toml`)
```toml
[build]
builder = "dockerfile"

[deploy]
healthcheckPath = "/"
healthcheckTimeout = 100
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[env]
NODE_ENV = "production"
HOST = "0.0.0.0"
```

## Database Migrations

Migrations run automatically on backend startup via Procfile:
```
web: alembic upgrade head && gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

## Monitoring

### View Logs
```bash
railway logs --service backend
railway logs --service frontend
```

### Health Checks
- Backend: `GET /api/health`
- Frontend: `GET /`

## Troubleshooting

### Frontend Static Files 404
The Dockerfile creates a symlink to fix Nuxt static file resolution:
```dockerfile
RUN mkdir -p .output/server/chunks && \
    ln -s ../../public .output/server/chunks/public
```

### Database Connection Issues
Ensure `DATABASE_URL` is properly set and the PostgreSQL service is running.

### CORS Errors
1. Check `CORS_ORIGINS` includes the frontend URL
2. Ensure `BACKEND_URL` is set correctly
3. Redeploy backend after changes

### Image Upload Issues
1. Verify AWS credentials are set
2. Check S3 bucket permissions
3. Images are stored at: `s3://aipijaca/assets/images/business_logos/`

## Quick Reference - Environment Variables

| Variable | Service | Required | Description |
|----------|---------|----------|-------------|
| DATABASE_URL | Backend | Yes | PostgreSQL connection string |
| SESSION_SECRET | Backend | Yes | Flask session secret |
| JWT_SECRET | Backend | Yes | JWT signing secret |
| CORS_ORIGINS | Backend | Yes | Frontend URL for CORS |
| BACKEND_URL | Backend | Yes | Backend public URL |
| AWS_ACCESS_KEY_ID | Backend | Yes | AWS credentials for S3 |
| AWS_SECRET_ACCESS_KEY | Backend | Yes | AWS credentials for S3 |
| AWS_S3_BUCKET | Backend | Yes | S3 bucket name |
| OPENAI_API_KEY | Backend | Yes | OpenAI API key |
| NUXT_PUBLIC_API_URL | Frontend | Yes | Backend API URL |
| ADMIN_PASSWORD | Backend | No | Initial admin password |
| INFOBIP_API_KEY | Backend | No | SMS service |
