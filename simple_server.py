#!/usr/bin/env python3
"""
Minimal HTTP server for Creator-VRidge AI without external dependencies
Uses only Python standard library
"""

import json
import os
import time
import random
import urllib.request
import urllib.parse
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging
import hashlib
import hmac
from datetime import datetime, timedelta

# Load environment variables
def load_env():
    """Load environment variables from .env file"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        logger.warning("No .env file found, using system environment variables")

load_env()

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# Security Configuration
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY must be at least 32 characters long")

# Creator-VRidge API configuration
CREATOR_VRIDGE_API_BASE = os.environ.get('CREATOR_VRIDGE_API_BASE', 'http://localhost:3001/api')
CREATOR_VRIDGE_API_TOKEN = os.environ.get('CREATOR_VRIDGE_API_TOKEN')

def get_fresh_token():
    """Creator-VRidge APIから最新のトークンを取得"""
    try:
        token_url = f"{CREATOR_VRIDGE_API_BASE}/ai-integration/token"
        response = urllib.request.urlopen(token_url, timeout=10)
        data = json.loads(response.read().decode())
        return data.get('token')
    except Exception as e:
        logger.error(f"Failed to get fresh token: {e}")
        return None

def load_creator_vridge_config():
    """Creator-VRidge APIから設定を自動取得"""
    try:
        config_url = f"{CREATOR_VRIDGE_API_BASE}/ai-integration/config"
        response = urllib.request.urlopen(config_url, timeout=10)
        config_data = json.loads(response.read().decode())

        # トークンを取得
        token = get_fresh_token()
        if not token:
            logger.warning("Failed to get fresh token, using environment variable")
            token = CREATOR_VRIDGE_API_TOKEN

        return {
            'base_url': config_data.get('config', {}).get('baseUrl', CREATOR_VRIDGE_API_BASE),
            'token': token,
            'endpoints': config_data.get('config', {}).get('endpoints', {})
        }
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        # Fallback to environment variables
        return {
            'base_url': CREATOR_VRIDGE_API_BASE,
            'token': CREATOR_VRIDGE_API_TOKEN,
            'endpoints': {}
        }

# Load dynamic configuration
try:
    dynamic_config = load_creator_vridge_config()
    CREATOR_VRIDGE_API_BASE = dynamic_config['base_url']
    CREATOR_VRIDGE_API_TOKEN = dynamic_config['token']
    logger.info("Successfully loaded dynamic configuration from Creator-VRidge API")
except Exception as e:
    logger.warning(f"Using fallback configuration: {e}")

if not CREATOR_VRIDGE_API_TOKEN:
    raise ValueError("CREATOR_VRIDGE_API_TOKEN could not be obtained from API or environment variables")

# Server configuration
SERVER_HOST = os.environ.get('SERVER_HOST', '127.0.0.1')
SERVER_PORT = int(os.environ.get('SERVER_PORT', 8000))
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# CORS configuration
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', 100))
RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', 3600))

# Rate limiting storage
rate_limit_storage = {}

def check_rate_limit(client_ip):
    """Simple rate limiting check"""
    current_time = time.time()
    window_start = current_time - RATE_LIMIT_WINDOW
    
    if client_ip not in rate_limit_storage:
        rate_limit_storage[client_ip] = []
    
    # Remove old requests
    rate_limit_storage[client_ip] = [
        req_time for req_time in rate_limit_storage[client_ip] 
        if req_time > window_start
    ]
    
    # Check if limit exceeded
    if len(rate_limit_storage[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request
    rate_limit_storage[client_ip].append(current_time)
    return True

def validate_api_key(api_key):
    """Validate API key (simple implementation)"""
    if not api_key:
        return False
    
    # For demo purposes, accept any key that starts with 'ai-api-'
    # In production, use proper key validation
    return api_key.startswith('ai-api-') and len(api_key) > 10

def sanitize_input(data):
    """Basic input sanitization"""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized[key] = value.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            elif isinstance(value, (int, float)):
                sanitized[key] = value
            elif isinstance(value, list):
                sanitized[key] = [sanitize_input(item) for item in value]
        return sanitized
    elif isinstance(data, str):
        return data.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    return data

class CreatorInsightHandler(BaseHTTPRequestHandler):
    """Secure HTTP handler for Creator Insight API"""
    
    def add_security_headers(self):
        """Add security headers to response"""
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        
        # CORS headers with proper validation
        origin = self.headers.get('Origin')
        if origin and origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Credentials', 'true')
        
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
    
    def check_authentication(self):
        """Check API key authentication"""
        api_key = self.headers.get('X-API-Key')
        if not validate_api_key(api_key):
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.add_security_headers()
            self.end_headers()
            error_response = {
                "error": "Unauthorized",
                "message": "Valid API key required"
            }
            self.wfile.write(json.dumps(error_response).encode())
            return False
        return True
    
    def check_rate_limit_for_request(self):
        """Check rate limiting for current request"""
        client_ip = self.client_address[0]
        if not check_rate_limit(client_ip):
            self.send_response(429)
            self.send_header('Content-type', 'application/json')
            self.add_security_headers()
            self.end_headers()
            error_response = {
                "error": "Rate limit exceeded",
                "message": f"Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds"
            }
            self.wfile.write(json.dumps(error_response).encode())
            return False
        return True
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.add_security_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        # Check rate limiting first
        if not self.check_rate_limit_for_request():
            return
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.add_security_headers()
            self.end_headers()
            response = {
                "message": "Creator-VRidge AI Recommendation System",
                "version": "1.0.0-secure",
                "status": "running"
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.add_security_headers()
            self.end_headers()
            response = {
                "status": "healthy",
                "security": "enabled"
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif path.startswith('/api/v1/recommendations/artworks'):
            # Check authentication for protected endpoints
            if not self.check_authentication():
                return
            self.handle_artwork_recommendations()
        elif path.startswith('/api/v1/recommendations'):
            if not self.check_authentication():
                return
            self.handle_recommendations()
            
        elif path.startswith('/api/v1/images'):
            if not self.check_authentication():
                return
            self.handle_images()
            
        elif path.startswith('/api/v1/analytics'):
            if not self.check_authentication():
                return
            self.handle_analytics()
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.add_security_headers()
            self.end_headers()
            response = {"error": "Not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        # Check rate limiting first
        if not self.check_rate_limit_for_request():
            return
        
        # Check authentication for all POST requests
        if not self.check_authentication():
            return
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Get request body with size limit
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 1024 * 1024:  # 1MB limit
            self.send_response(413)
            self.send_header('Content-type', 'application/json')
            self.add_security_headers()
            self.end_headers()
            response = {"error": "Request too large"}
            self.wfile.write(json.dumps(response).encode())
            return
        
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode()) if post_data else {}
            # Sanitize input data
            data = sanitize_input(data)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.add_security_headers()
            self.end_headers()
            response = {"error": "Invalid JSON"}
            self.wfile.write(json.dumps(response).encode())
            return
        
        if path.startswith('/api/v1/recommendations/artworks'):
            self.handle_artwork_recommendations_post(data)
        elif path.startswith('/api/v1/recommendations'):
            self.handle_recommendations_post(data)
        elif path.startswith('/api/v1/images'):
            self.handle_images_post(data)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.add_security_headers()
            self.end_headers()
            response = {"error": "Not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def handle_recommendations(self):
        """Handle recommendation requests"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Mock recommendation data
        recommendations = {
            "recommendations": [
                {
                    "id": 1,
                    "title": "Abstract Art Style",
                    "score": 0.95,
                    "description": "Modern abstract painting techniques"
                },
                {
                    "id": 2,
                    "title": "Digital Portrait",
                    "score": 0.87,
                    "description": "Digital art portrait techniques"
                }
            ],
            "total": 2
        }
        self.wfile.write(json.dumps(recommendations).encode())
    
    def handle_artwork_recommendations(self):
        """Handle GET requests for artwork recommendations"""
        try:
            # Get artwork recommendations from API
            artworks = self.generate_mock_artworks(6)
            recommendations = []
            
            for i, artwork in enumerate(artworks):
                recommendations.append({
                    "artwork": artwork,
                    "score": round(random.uniform(0.7, 0.99), 2),
                    "recommendation_id": f"rec_{int(time.time())}_{i}",
                    "position": i + 1,
                    "reason": self.generate_reason(artwork)
                })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "recommendations": recommendations,
                "total": len(recommendations),
                "algorithm": "ai_collaborative_filtering"
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            # Log detailed error but don't expose it
            logger.error(f"Failed to get artwork recommendations: {str(e)}")
            if DEBUG:
                logger.debug(f"Exception details: {e}")
            
            self.send_response(503)
            self.send_header('Content-type', 'application/json')
            self.add_security_headers()
            self.end_headers()
            error_response = {
                "error": "Service unavailable",
                "message": "Unable to process request"
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def handle_artwork_recommendations_post(self, data):
        """Handle POST requests for artwork recommendations"""
        try:
            # Extract user preferences
            user_id = data.get('user_id', 'anonymous')
            limit = data.get('limit', 10)
            
            # Get artwork recommendations from API based on user preferences
            artworks = self.generate_mock_artworks(limit)
            recommendations = []
            
            for i, artwork in enumerate(artworks):
                recommendations.append({
                    "artwork": artwork,
                    "score": round(random.uniform(0.7, 0.99), 2),
                    "recommendation_id": f"rec_{int(time.time())}_{i}",
                    "position": i + 1,
                    "reason": self.generate_reason(artwork)
                })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "recommendations": recommendations,
                "total": len(recommendations),
                "algorithm": "ai_collaborative_filtering"
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            # Log detailed error but don't expose it
            logger.error(f"Failed to get artwork recommendations: {str(e)}")
            if DEBUG:
                logger.debug(f"Exception details: {e}")
            
            self.send_response(503)
            self.send_header('Content-type', 'application/json')
            self.add_security_headers()
            self.end_headers()
            error_response = {
                "error": "Service unavailable",
                "message": "Unable to process request"
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def generate_mock_artworks(self, count):
        """Get artwork data from creator-vridge API"""
        # Try to get artworks from creator-vridge API
        api_url = f"{CREATOR_VRIDGE_API_BASE}/recommendations/artworks?limit={count}"
        
        # Use token from environment variables
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CREATOR_VRIDGE_API_TOKEN}',
            'Origin': 'http://localhost:3000'
        }
        
        request = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return self.map_api_artworks_to_format(data.get('recommendations', []))
            else:
                raise Exception(f"API returned status {response.status}")
    
    def map_api_artworks_to_format(self, api_artworks):
        """Map API response format to our expected format"""
        artworks = []
        for item in api_artworks:
            artwork = {
                "id": item.get("id"),
                "title": item.get("title", "無題"),
                "imageUrl": item.get("imageUrl", ""),
                "thumbnailUrl": item.get("thumbnailUrl", ""),
                "category": item.get("category", "ILLUSTRATION"),
                "style": item.get("style", "anime"),
                "tags": item.get("tags", []),
                "artistUserId": item.get("artist", {}).get("id", "unknown"),
                "createdAt": item.get("createdAt", "2025-09-21T10:00:00.000Z")
            }
            artworks.append(artwork)
        return artworks
    
    def generate_reason(self, artwork):
        """Generate recommendation reason based on artwork"""
        style = artwork["style"]
        category = artwork["category"]
        
        reasons = [
            f"あなたの好みの{style}スタイルです",
            f"{category}カテゴリーでおすすめの作品です",
            f"類似した{style}作品を閲覧された履歴があります",
            f"人気の{category}作品です",
            f"あなたがフォローしているアーティストの{style}作品に類似しています"
        ]
        
        return random.choice(reasons)
    
    def handle_recommendations_post(self, data):
        """Handle POST requests for recommendations"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Mock processing of user preferences
        response = {
            "message": "Recommendations updated",
            "user_preferences": data,
            "recommendations_count": 5
        }
        self.wfile.write(json.dumps(response).encode())
    
    def handle_images(self):
        """Handle image requests"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        images = {
            "images": [
                {
                    "id": 1,
                    "url": "/mock/image1.jpg",
                    "title": "Sample Artwork 1",
                    "artist": "AI Generated"
                },
                {
                    "id": 2,
                    "url": "/mock/image2.jpg", 
                    "title": "Sample Artwork 2",
                    "artist": "AI Generated"
                }
            ],
            "total": 2
        }
        self.wfile.write(json.dumps(images).encode())
    
    def handle_images_post(self, data):
        """Handle POST requests for images"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "message": "Image processed",
            "image_data": data,
            "analysis": "Mock analysis complete"
        }
        self.wfile.write(json.dumps(response).encode())
    
    def handle_analytics(self):
        """Handle analytics requests"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        analytics = {
            "analytics": {
                "total_requests": 100,
                "active_users": 25,
                "popular_styles": ["Abstract", "Portrait", "Landscape"]
            }
        }
        self.wfile.write(json.dumps(analytics).encode())
    
    def log_message(self, format, *args):
        """Override log message to use Python logging"""
        logger.info("%s - - [%s] %s" % 
                   (self.address_string(),
                    self.log_date_time_string(),
                    format % args))

def setup_database():
    """Setup minimal SQLite database"""
    if not os.path.exists('creator_insight_minimal.db'):
        conn = sqlite3.connect('creator_insight_minimal.db')
        cursor = conn.cursor()
        
        # Create basic tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY,
                title TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                title TEXT,
                score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")

def run_server():
    """Run the secure server"""
    setup_database()
    
    server_address = (SERVER_HOST, SERVER_PORT)
    httpd = HTTPServer(server_address, CreatorInsightHandler)
    
    logger.info(f"Starting Creator-VRidge AI secure server on {SERVER_HOST}:{SERVER_PORT}")
    logger.info(f"Security features enabled:")
    logger.info(f"  - API key authentication: Required")
    logger.info(f"  - Rate limiting: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s")
    logger.info(f"  - CORS origins: {ALLOWED_ORIGINS}")
    logger.info(f"  - Debug mode: {DEBUG}")
    logger.info("Available endpoints (require X-API-Key header):")
    logger.info("  GET  / - Health check (public)")
    logger.info("  GET  /health - System health (public)")
    logger.info("  GET  /api/v1/recommendations/artworks - Get artwork recommendations")
    logger.info("  POST /api/v1/recommendations/artworks - Get artwork recommendations with preferences")
    logger.info("  GET  /api/v1/analytics - Get analytics")
    logger.info("Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
        httpd.server_close()

if __name__ == "__main__":
    run_server()