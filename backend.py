# requirements.txt
flask==2.3.3
flask-sqlalchemy==3.0.5
flask-cors==4.0.0
flask-jwt-extended==4.5.3
werkzeug==2.3.7
requests==2.31.0
google-generativeai==0.3.0
python-dotenv==1.0.0
bcrypt==4.0.1

# run.py
from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///research_bot.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('SECRET_KEY', 'jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, origins=["http://localhost:3000", "https://*.vercel.app"])
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.chat import chat_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

# app/models/user.py
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    chats = db.relationship('Chat', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

# app/models/chat.py
from app import db
from datetime import datetime
import json

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    sources = db.Column(db.Text)  # JSON string of sources
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_sources(self, sources_list):
        self.sources = json.dumps(sources_list)
    
    def get_sources(self):
        if self.sources:
            return json.loads(self.sources)
        return []
    
    def to_dict(self):
        return {
            'id': self.id,
            'query': self.query,
            'response': self.response,
            'sources': self.get_sources(),
            'created_at': self.created_at.isoformat()
        }

# app/routes/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'All fields are required'}), 400
        
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if user exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create user
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'User created successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'valid': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# app/routes/chat.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.chat import Chat
from app.services.agent_service import ResearchAgent

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/search', methods=['POST'])
@jwt_required()
def search_query():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Initialize research agent
        agent = ResearchAgent()
        
        # Get AI-powered research results
        result = agent.research_query(query)
        
        # Save to database
        chat = Chat(
            user_id=current_user_id,
            query=query,
            response=result['response']
        )
        chat.set_sources(result['sources'])
        
        db.session.add(chat)
        db.session.commit()
        
        return jsonify({
            'response': result['response'],
            'sources': result['sources'],
            'query': query,
            'chat_id': chat.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    try:
        current_user_id = get_jwt_identity()
        
        chats = Chat.query.filter_by(user_id=current_user_id)\
                          .order_by(Chat.created_at.desc())\
                          .limit(50).all()
        
        return jsonify({
            'history': [chat.to_dict() for chat in chats]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/clear', methods=['DELETE'])
@jwt_required()
def clear_history():
    try:
        current_user_id = get_jwt_identity()
        
        Chat.query.filter_by(user_id=current_user_id).delete()
        db.session.commit()
        
        return jsonify({'message': 'Chat history cleared'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# app/services/gemini_service.py
import google.generativeai as genai
import os

class GeminiService:
    def __init__(self):
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_search_queries(self, user_query):
        """Generate optimized search queries from user input"""
        prompt = f"""
        As a research assistant, analyze this user query and generate 3-5 optimized search queries 
        that would help find the most relevant academic articles, reports, and authoritative sources.
        
        User Query: "{user_query}"
        
        Generate search queries that are:
        1. Specific and targeted for academic/professional research
        2. Include relevant keywords and synonyms
        3. Suitable for finding recent articles, reports, and studies
        
        Format as a JSON array of strings:
        ["query1", "query2", "query3"]
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response
            import json
            queries_text = response.text.strip()
            if queries_text.startswith('```'):
                queries_text = queries_text.split('```')[1].strip()
                if queries_text.startswith('json'):
                    queries_text = queries_text[4:].strip()
            
            queries = json.loads(queries_text)
            return queries[:5]  # Limit to 5 queries
        except Exception as e:
            # Fallback to original query
            return [user_query]
    
    def synthesize_research_response(self, user_query, search_results):
        """Synthesize search results into a comprehensive research response"""
        sources_text = ""
        for i, result in enumerate(search_results[:10], 1):
            sources_text += f"{i}. {result.get('title', 'N/A')}\n   {result.get('snippet', 'N/A')}\n   URL: {result.get('link', 'N/A')}\n\n"
        
        prompt = f"""
        As a research assistant helping writers and researchers, synthesize the following search results 
        into a comprehensive, well-structured response for the user's query.
        
        User Query: "{user_query}"
        
        Search Results:
        {sources_text}
        
        Instructions:
        1. Provide a clear, informative response that directly addresses the user's query
        2. Organize information logically with clear sections if needed
        3. Highlight key findings, trends, or insights from the sources
        4. Be objective and cite-focused (don't include actual citations, just synthesize)
        5. End with a brief summary of the most valuable resources found
        6. Keep the response research-focused and professional
        7. If the query is about recent events or developments, emphasize the most current information
        
        Write a comprehensive response (200-400 words):
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"I found several relevant sources for your query about '{user_query}'. Please review the sources below for detailed information."

# app/services/search_service.py
import requests
import os

class SearchService:
    def __init__(self):
        self.api_key = os.environ.get('SERPAPI_KEY')
        self.base_url = "https://serpapi.com/search"
    
    def search(self, query, num_results=10):
        """Search the web using SerpAPI"""
        params = {
            'q': query,
            'api_key': self.api_key,
            'engine': 'google',
            'num': num_results,
            'safe': 'active'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract organic results
            results = []
            organic_results = data.get('organic_results', [])
            
            for result in organic_results:
                results.append({
                    'title': result.get('title', 'No Title'),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', 'No description available'),
                    'source': result.get('displayed_link', ''),
                    'date': result.get('date', '')
                })
            
            return results
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []

# app/services/agent_service.py
from app.services.gemini_service import GeminiService
from app.services.search_service import SearchService
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ResearchAgent:
    def __init__(self):
        self.gemini = GeminiService()
        self.search = SearchService()
    
    def research_query(self, user_query):
        """Main research method that combines AI and search"""
        try:
            # Step 1: Generate optimized search queries
            search_queries = self.gemini.generate_search_queries(user_query)
            
            # Step 2: Perform searches
            all_results = []
            for query in search_queries:
                results = self.search.search(query, num_results=8)
                all_results.extend(results)
            
            # Remove duplicates based on URL
            unique_results = []
            seen_urls = set()
            for result in all_results:
                if result['link'] not in seen_urls and result['link']:
                    unique_results.append(result)
                    seen_urls.add(result['link'])
            
            # Limit to top 15 results
            unique_results = unique_results[:15]
            
            # Step 3: Synthesize response
            ai_response = self.gemini.synthesize_research_response(user_query, unique_results)
            
            return {
                'response': ai_response,
                'sources': unique_results,
                'search_queries_used': search_queries
            }
            
        except Exception as e:
            return {
                'response': f"I apologize, but I encountered an error while researching your query: {str(e)}. Please try again or rephrase your question.",
                'sources': [],
                'search_queries_used': [user_query]
            }

# app/utils/helpers.py
from datetime import datetime
import re

def clean_text(text):
    """Clean and format text for display"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove HTML tags if any
    text = re.sub('<[^<]+?>', '', text)
    
    return text.strip()

def format_sources(sources):
    """Format sources for better display"""
    formatted = []
    for source in sources:
        formatted.append({
            'title': clean_text(source.get('title', 'Untitled')),
            'url': source.get('link', ''),
            'description': clean_text(source.get('snippet', '')),
            'domain': source.get('source', ''),
            'date': source.get('date', '')
        })
    return formatted
