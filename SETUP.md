# AI Pijaca - Setup Guide

Complete guide to set up and run the AI Pijaca application locally and deploy to production.

## Project Overview

This is a full-stack application with:
- **Frontend**: Nuxt.js 3 with Tailwind CSS (Vue 3, TypeScript)
- **Backend**: Flask with SQLAlchemy (Python, PostgreSQL)
- **AI Features**: Anthropic Claude API for chat and product recommendations

## Prerequisites

Before you begin, ensure you have:

- **Node.js** 18+ and npm (for frontend)
- **Python** 3.9+ (for backend)
- **PostgreSQL** (optional, SQLite works for development)
- **Git** for version control

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-market-v2

# Copy environment files
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env

# Edit the .env files with your API keys and configuration

# Start all services
docker-compose up

# Frontend: http://localhost:3000
# Backend: http://localhost:5000
# Database: PostgreSQL on port 5432
```

### Option 2: Manual Setup

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy and configure environment
cp .env.example .env

# Edit .env and set:
# NUXT_PUBLIC_API_BASE=http://localhost:5000

# Run development server
npm run dev

# Frontend will be available at http://localhost:3000
```

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env

# Edit .env and set your API keys and database URL

# Run Flask server
python app.py

# Backend will be available at http://localhost:5000
```

## Environment Variables

### Frontend (.env)

```bash
NUXT_PUBLIC_API_BASE=http://localhost:5000
```

### Backend (.env)

**Required:**
```bash
SESSION_SECRET=your-random-secret-key-here
DATABASE_URL=sqlite:///marketplace.db  # or PostgreSQL URL
```

**For AI Features:**
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
```

**For Google OAuth:**
```bash
AI_PIJACA_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
AI_PIJACA_GOOGLE_CLIENT_SECRET=your-client-secret
```

**For Email (SendGrid):**
```bash
SENDGRID_API_KEY=SG.xxxxx
SENDGRID_FROM_EMAIL=noreply@aipijaca.com
```

## Database Setup

### SQLite (Development)

SQLite is used by default. Database file will be created automatically at `backend/instance/marketplace.db`.

### PostgreSQL (Production)

```bash
# Create database
createdb aimarket

# Update .env
DATABASE_URL=postgresql://username:password@localhost:5432/aimarket

# Tables will be created automatically on first run
```

## Features

### Frontend Features

- ✅ Modern, responsive UI with Tailwind CSS
- ✅ Dark mode support
- ✅ AI Chat interface
- ✅ Product browsing and search
- ✅ User authentication (Google OAuth + Email)
- ✅ Professional design inspired by Linear, Vercel, Claude.ai
- ✅ Glass morphism and gradient effects
- ✅ Smooth animations and transitions

### Backend Features

- ✅ Flask REST API
- ✅ SQLAlchemy ORM with PostgreSQL/SQLite
- ✅ User authentication and session management
- ✅ Google OAuth integration
- ✅ AI-powered chat using Anthropic Claude
- ✅ Product search and recommendations
- ✅ Business and product management
- ✅ Email notifications with SendGrid

## API Endpoints

### Authentication
- `POST /auth/login` - Email/password login
- `GET /auth/google` - Google OAuth
- `GET /auth/verify` - Verify token
- `POST /auth/logout` - Logout

### Products
- `GET /api/products` - List products
- `GET /api/products/:id` - Get product details
- `POST /api/products` - Create product (auth required)
- `PUT /api/products/:id` - Update product (auth required)

### Chat
- `POST /api/chat` - Send message to AI assistant

## Development

### Frontend Development

```bash
cd frontend

# Run dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Generate static site
npm run generate
```

### Backend Development

```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run with auto-reload
FLASK_ENV=development python app.py

# Run tests (if available)
pytest
```

## Deployment

### Frontend Deployment (Vercel/Netlify)

```bash
cd frontend

# Build
npm run build

# Deploy to Vercel
npx vercel --prod

# Or deploy to Netlify
npx netlify deploy --prod --dir=.output/public
```

### Backend Deployment (Railway/Heroku)

The backend is configured for Railway deployment with `railway.json`:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

For Heroku:

```bash
# Create Procfile
echo "web: gunicorn app:app" > backend/Procfile

# Deploy
git push heroku main
```

### Environment Variables on Railway/Heroku

Set all required environment variables from `.env.example` in your deployment platform's dashboard.

## Project Structure

```
ai-market-v2/
├── frontend/                 # Nuxt.js frontend
│   ├── assets/              # CSS, images
│   ├── components/          # Vue components
│   │   ├── layout/         # Header, Footer
│   │   ├── chat/           # Chat interface
│   │   └── ui/             # Buttons, inputs
│   ├── composables/        # Vue composables
│   ├── layouts/            # Page layouts
│   ├── pages/              # Routes
│   ├── public/             # Static files
│   └── nuxt.config.ts      # Nuxt configuration
│
├── backend/                 # Flask backend
│   ├── auth/               # Auth routes
│   ├── api/                # API endpoints
│   ├── services/           # Business logic
│   ├── app.py              # Flask app
│   ├── models.py           # Database models
│   ├── routes.py           # Route handlers
│   └── requirements.txt    # Python dependencies
│
├── docker-compose.yml      # Docker configuration
└── README.md              # Project documentation
```

## Troubleshooting

### Frontend Issues

**Port 3000 already in use:**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

**Module not found:**
```bash
rm -rf node_modules package-lock.json
npm install
```

### Backend Issues

**Database connection error:**
- Check DATABASE_URL in .env
- Ensure PostgreSQL is running (if using PostgreSQL)
- For SQLite, check that `backend/instance/` directory exists

**Import errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Port 5000 already in use:**
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

## Getting API Keys

### Anthropic Claude API
1. Go to https://console.anthropic.com/
2. Create an account
3. Generate API key
4. Add to .env: `ANTHROPIC_API_KEY=sk-ant-xxxxx`

### OpenAI API
1. Go to https://platform.openai.com/
2. Create account and add payment method
3. Generate API key
4. Add to .env: `OPENAI_API_KEY=sk-xxxxx`

### Google OAuth
1. Go to https://console.cloud.google.com/
2. Create project
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:5000/auth/google/authorized`
6. Add to .env

### SendGrid
1. Go to https://sendgrid.com/
2. Create account
3. Generate API key
4. Add to .env: `SENDGRID_API_KEY=SG.xxxxx`

## Support

For issues or questions:
- Check existing issues
- Review documentation
- Contact development team

## License

Private - All Rights Reserved
