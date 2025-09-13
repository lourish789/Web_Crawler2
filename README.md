# Web_Crawler2

# Research Chatbot - Deployment & Setup Guide

## 🚀 Quick Start Guide

### Prerequisites
- Node.js (v16 or higher)
- Python (v3.8 or higher)
- Git
- Gemini API Key (Google AI Studio)
- SerpAPI Key

### 1. Get API Keys

#### Gemini API Key (Free)
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Create new API key
4. Copy the key

#### SerpAPI Key (Free tier: 100 searches/month)
1. Visit [SerpAPI](https://serpapi.com)
2. Sign up for free account
3. Get your API key from dashboard

### 2. Backend Setup

```bash
# Clone/create project directory
mkdir research-chatbot
cd research-chatbot

# Create backend directory
mkdir backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies (create requirements.txt first)
pip install -r requirements.txt

# Create .env file
touch .env
```

**Backend .env file:**
```env
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-here-change-this-in-production
GEMINI_API_KEY=your-gemini-api-key-here
SERPAPI_KEY=your-serpapi-key-here
DATABASE_URL=sqlite:///research_bot.db
```

```bash
# Run the backend
python run.py
```

### 3. Frontend Setup

```bash
# From project root, create frontend
cd ../
npx create-react-app frontend
cd frontend

# Install additional dependencies
npm install react-router-dom axios lucide-react

# Create .env file
touch .env
```

**Frontend .env file:**
```env
REACT_APP_API_URL=http://localhost:5000
```

```bash
# Replace src files with provided code
# Then start the frontend
npm start
```

### 4. Testing Locally

1. Start backend: `python run.py` (runs on port 5000)
2. Start frontend: `npm start` (runs on port 3000)
3. Visit `http://localhost:3000`
4. Create account and test the chat

## 🌐 Free Deployment Options

### Option 1: Vercel (Frontend) + Railway (Backend)

#### Deploy Backend to Railway
1. Create account at [Railway](https://railway.app)
2. Connect GitHub repository
3. Create new project from GitHub repo
4. Set environment variables in Railway dashboard:
   - `SECRET_KEY`
   - `GEMINI_API_KEY`
   - `SERPAPI_KEY`
   - `DATABASE_URL=postgresql://...` (Railway provides PostgreSQL)
5. Deploy automatically on push

#### Deploy Frontend to Vercel
1. Create account at [Vercel](https://vercel.com)
2. Connect GitHub repository
3. Set build settings:
   - Build Command: `npm run build`
   - Output Directory: `build`
4. Set environment variables:
   - `REACT_APP_API_URL=https://your-railway-app.railway.app`
5. Deploy automatically on push

### Option 2: Netlify (Frontend) + Heroku (Backend)

#### Deploy Backend to Heroku
```bash
# Install Heroku CLI
# Create Procfile in backend root:
echo "web: python run.py" > Procfile

# Initialize git and deploy
git init
git add .
git commit -m "Initial commit"
heroku create your-app-name
git push heroku main

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set GEMINI_API_KEY=your-gemini-key
heroku config:set SERPAPI_KEY=your-serpapi-key
```

#### Deploy Frontend to Netlify
1. Build the frontend: `npm run build`
2. Drag and drop the `build` folder to Netlify
3. Or connect GitHub for automatic deploys

### Option 3: All-in-One with Render

1. Create account at [Render](https://render.com)
2. Create PostgreSQL database (free)
3. Create web service for backend
4. Create static site for frontend

## 🔧 Production Optimizations

### Backend (.env for production)
```env
FLASK_ENV=production
SECRET_KEY=super-strong-secret-key-minimum-32-characters
GEMINI_API_KEY=your-gemini-api-key
SERPAPI_KEY=your-serpapi-key
DATABASE_URL=postgresql://username:password@host:port/database
```

### Frontend Build Optimizations
```json
// package.json - add to scripts
{
  "build": "react-scripts build && echo 'Build completed!'",
  "build:analyze": "npm run build && npx source-map-explorer 'build/static/js/*.js'"
}
```

### Database Migration (SQLite to PostgreSQL)
```python
# In your backend, update config for production
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///research_bot.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

## 📊 Monitoring & Analytics

### Add Error Tracking (Optional)
```bash
# Backend
pip install sentry-sdk[flask]

# Frontend
npm install @sentry/react @sentry/tracing
```

### Performance Monitoring
- Use built-in Railway/Heroku metrics
- Google Analytics for frontend
- Backend logging with structured logs

## 🔒 Security Best Practices

### Environment Variables
- Never commit `.env` files
- Use strong, unique secrets
- Rotate API keys regularly

### CORS Configuration
```python
# In app/__init__.py
CORS(app, origins=[
    "https://your-frontend-domain.vercel.app",
    "https://your-custom-domain.com"
])
```

### Rate Limiting (Optional)
```python
# Install flask-limiter
pip install Flask-Limiter

# Add to your app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

## 🚨 Troubleshooting

### Common Issues

**Backend won't start:**
- Check Python version (3.8+)
- Verify all environment variables
- Check port availability

**Frontend won't connect:**
- Verify REACT_APP_API_URL is correct
- Check CORS settings
- Ensure backend is running

**API Keys not working:**
- Verify keys are correct and active
- Check API quotas
- Ensure keys have proper permissions

**Database errors:**
- For SQLite: check file permissions
- For PostgreSQL: verify connection string
- Run migrations if needed

### Debug Mode
```bash
# Backend debug
export FLASK_DEBUG=1
python run.py

# Frontend debug
npm start
# Check browser console for errors
```

## 📈 Scaling Considerations

### Free Tier Limits
- **Vercel**: 100GB bandwidth/month
- **Railway**: 500 hours runtime/month
- **Heroku**: 550 hours/month (sleeps after 30min inactivity)
- **Gemini API**: High free quota
- **SerpAPI**: 100 searches/month free

### Upgrade Path
1. **Database**: SQLite → PostgreSQL → Managed DB
2. **Hosting**: Free tier → Paid plans → Custom servers
3. **CDN**: Add Cloudflare for better performance
4. **Caching**: Redis for session management
5. **Search**: Consider adding Elasticsearch for chat history

## 📝 Maintenance

### Regular Tasks
- Monitor API usage and costs
- Update dependencies monthly
- Backup database regularly
- Review and rotate secrets
- Monitor error logs

### Updates
```bash
# Backend dependencies
pip list --outdated
pip install --upgrade package-name

# Frontend dependencies
npm outdated
npm update
```

This guide provides everything needed to deploy and maintain your research chatbot on free platforms! 🎉
