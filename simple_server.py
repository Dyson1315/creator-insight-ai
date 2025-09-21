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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Creator-VRidge API configuration
CREATOR_VRIDGE_API_BASE = "http://localhost:3001/api"

class CreatorInsightHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler for Creator Insight API"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "message": "Creator-VRidge AI Recommendation System (Minimal)",
                "version": "1.0.0-minimal",
                "status": "running"
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "database": "sqlite (minimal)",
                "ml_models": "mock"
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif path.startswith('/api/v1/recommendations/artworks'):
            self.handle_artwork_recommendations()
        elif path.startswith('/api/v1/recommendations'):
            self.handle_recommendations()
            
        elif path.startswith('/api/v1/images'):
            self.handle_images()
            
        elif path.startswith('/api/v1/analytics'):
            self.handle_analytics()
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"error": "Not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Get request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode()) if post_data else {}
        except json.JSONDecodeError:
            data = {}
        
        if path.startswith('/api/v1/recommendations/artworks'):
            self.handle_artwork_recommendations_post(data)
        elif path.startswith('/api/v1/recommendations'):
            self.handle_recommendations_post(data)
        elif path.startswith('/api/v1/images'):
            self.handle_images_post(data)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
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
            logger.error(f"Failed to get artwork recommendations: {e}")
            self.send_response(503)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {
                "error": "Service unavailable",
                "message": "Unable to connect to Creator-VRidge API"
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
            logger.error(f"Failed to get artwork recommendations: {e}")
            self.send_response(503)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {
                "error": "Service unavailable",
                "message": "Unable to connect to Creator-VRidge API"
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def generate_mock_artworks(self, count):
        """Get artwork data from creator-vridge API"""
        # Try to get artworks from creator-vridge API
        api_url = f"{CREATOR_VRIDGE_API_BASE}/v1/artworks/recommendations?limit={count}"
        
        # Use valid AI user token
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI1NWNmYzkwMC05N2JkLTQ3ZWYtYjk2Ni1lMzlmZTQzYmE2YWYiLCJ1c2VyVHlwZSI6IkFJIiwiZW1haWwiOiJhaS1hcGlAY3JlYXRvci12cmlkZ2UuY29tIiwiaWF0IjoxNzU4NDgwODIxLCJleHAiOjE3NTkwODU2MjEsImF1ZCI6ImNyZWF0b3J2cmlkZ2UtYXBwIiwiaXNzIjoiY3JlYXRvcnZyaWRnZS1hcGkifQ.47X_Gn3t8t4kXdSNZ9FxXqVwGyQjEac13b55h-9gpSw',
            'Origin': 'http://localhost:3000'
        }
        
        request = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(request, timeout=10) as response:
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

def run_server(port=8000):
    """Run the minimal server"""
    setup_database()
    
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, CreatorInsightHandler)
    
    logger.info(f"Starting Creator-VRidge AI minimal server on port {port}")
    logger.info(f"Access the API at: http://127.0.0.1:{port}")
    logger.info(f"Also available at: http://localhost:{port}")
    logger.info("Available endpoints:")
    logger.info("  GET  / - Health check")
    logger.info("  GET  /health - Detailed health")
    logger.info("  GET  /api/v1/recommendations - Get recommendations")
    logger.info("  POST /api/v1/recommendations - Update preferences")
    logger.info("  GET  /api/v1/recommendations/artworks - Get artwork recommendations")
    logger.info("  POST /api/v1/recommendations/artworks - Get artwork recommendations with preferences")
    logger.info("  GET  /api/v1/images - Get images")
    logger.info("  POST /api/v1/images - Process image")
    logger.info("  GET  /api/v1/analytics - Get analytics")
    logger.info("Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
        httpd.server_close()

if __name__ == "__main__":
    run_server()