# AI Pijaca - AI Market

AI-powered shopping assistant for Bosnia and Herzegovina. Find the best deals with intelligent product recommendations.

## Project Structure

```
ai-market-v2/
├── frontend/     # Nuxt.js frontend application
├── backend/      # Flask backend API
└── README.md
```

## Features

- **AI Chat Assistant**: Conversational interface for product discovery
- **Smart Search**: AI-powered product search with natural language understanding
- **Product Management**: Business dashboard for managing products
- **User Authentication**: Secure login with Google OAuth and email
- **Dark Mode**: Beautiful dark/light theme support
- **Responsive Design**: Works seamlessly on all devices

## Local Development

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- PostgreSQL (optional, SQLite used by default)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:3000
```

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
# Runs at http://localhost:5000
```

### Using Docker Compose (Recommended)

```bash
docker-compose up
# Frontend: http://localhost:3000
# Backend: http://localhost:5000
```

## Environment Variables

See `.env.example` files in each service directory for required configuration.

### Frontend (.env)
- `NUXT_PUBLIC_API_BASE` - Backend API URL

### Backend (.env)
- `DATABASE_URL` - PostgreSQL connection string
- `ANTHROPIC_API_KEY` - Claude API key for AI features
- `OPENAI_API_KEY` - OpenAI API key
- `SESSION_SECRET` - Secret key for sessions
- `AI_PIJACA_GOOGLE_CLIENT_ID` - Google OAuth client ID
- `AI_PIJACA_GOOGLE_CLIENT_SECRET` - Google OAuth secret

## Technology Stack

### Frontend
- **Nuxt.js 3** - Vue framework for production
- **Vue 3** - Progressive JavaScript framework
- **Tailwind CSS** - Utility-first CSS framework
- **TypeScript** - Type-safe JavaScript

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL** - Production database
- **Anthropic Claude** - AI language model
- **RAG** - Retrieval Augmented Generation for product matching

## Deployment

Both services can be deployed separately on platforms like Railway, Vercel, or similar:

- **Frontend**: Deploy the `/frontend` directory
- **Backend**: Deploy the `/backend` directory

Make sure to set environment variables in your deployment platform.

## Contributing

This is a private project. For questions or issues, contact the development team.

## License

Private - All Rights Reserved
