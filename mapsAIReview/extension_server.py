#!/usr/bin/env python3
"""
Flask server for Chrome extension integration.
This server acts as a bridge between the Chrome extension and the Python scraper.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from restaurant_review_scraper import RestaurantReviewScraper
import os
import traceback
import json
import tempfile
import sys

# Add ai_generation to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_generation'))

try:
    from ai_generation.main import run_ai_review
    ai_system_available = True
    print("✅ AI generation system loaded successfully")
except ImportError as e:
    print(f"⚠️  AI generation system not available: {e}")
    ai_system_available = False

app = Flask(__name__)
CORS(app)

try:
    scraper = RestaurantReviewScraper()
    print("✅ Scraper initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize scraper: {e}")
    scraper = None

def get_ai_response(question, reviews_data):
    """
    Integrate with the AI generation system to provide intelligent responses.
    """
    if not ai_system_available:
        restaurant_name = reviews_data.get('locationDetails', {}).get('title', 'this restaurant')
        total_reviews = len(reviews_data.get('reviews', []))
        avg_rating = reviews_data.get('review_stats', {}).get('average_rating', 0)
        
        return f"Thanks for asking about {restaurant_name}! I have {total_reviews} reviews to analyze (avg rating: {avg_rating:.1f}/5). [AI system not available - please check your .env file has OPENAI_API_KEY and COHERE_API_KEY configured.]"
    
    try:
        # Create a temporary JSON file with the reviews data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            json.dump(reviews_data, temp_file, indent=2, ensure_ascii=False)
            temp_file_path = temp_file.name
        
        print(f"🤖 Analyzing question with AI system...")
        print(f"📊 Using {len(reviews_data.get('reviews', []))} reviews for analysis")
        
        # Call the AI generation system
        ai_response = run_ai_review(temp_file_path, question)
        
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass  # File cleanup failed, but not critical
        
        print(f"✅ AI analysis completed")
        return ai_response
        
    except Exception as e:
        print(f"❌ AI analysis failed: {str(e)}")
        print(traceback.format_exc())
        
        # Fallback to basic response if AI fails
        restaurant_name = reviews_data.get('locationDetails', {}).get('title', 'this restaurant')
        total_reviews = len(reviews_data.get('reviews', []))
        
        return f"I'm sorry, I encountered an error while analyzing the reviews for {restaurant_name}. I have {total_reviews} reviews available, but the AI analysis system is currently unavailable. Error: {str(e)}"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'server': 'Restaurant Review Scraper',
        'version': '1.0',
        'scraper_available': scraper is not None
    })

@app.route('/chat', methods=['POST'])
def chat_about_restaurant():
    """Chat endpoint for asking questions about restaurants"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        question = data.get('question')
        restaurant_data = data.get('restaurant_data')
        url = data.get('url')
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        print(f"💬 Question: {question}")
        
        # Use pre-loaded restaurant data if provided, otherwise fetch it
        if restaurant_data:
            print(f"📊 Using pre-loaded data for: {restaurant_data.get('locationDetails', {}).get('title', 'Unknown')}")
            reviews_data = restaurant_data
        else:
            # Fallback to fetching data if not provided
            if not scraper:
                return jsonify({'error': 'Scraper not available. Check your .env file and API key.'}), 500
            
            if not url:
                return jsonify({'error': 'URL is required when restaurant_data not provided'}), 400
            
            print(f"🔄 Fetching data for {url[:60]}...")
            reviews_data = scraper.get_random_reviews(url, num_reviews=50)
        
        # Generate AI-powered response
        answer = get_ai_response(question, reviews_data)
        
        print(f"✅ Generated answer for question")
        
        return jsonify({
            'question': question,
            'answer': answer,
            'restaurant': reviews_data.get('locationDetails', {}),
            'context_reviews': len(reviews_data.get('reviews', []))
        })
        
    except ValueError as e:
        error_msg = str(e)
        print(f"❌ Validation error: {error_msg}")
        return jsonify({'error': error_msg}), 400
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/scrape', methods=['POST'])
def scrape_reviews():
    """Legacy endpoint for scraping reviews (kept for compatibility)"""
    try:
        if not scraper:
            return jsonify({'error': 'Scraper not available. Check your .env file and API key.'}), 500
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        url = data.get('url')
        num_reviews = data.get('num_reviews', 50)
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        try:
            num_reviews = int(num_reviews)
            if num_reviews < 1 or num_reviews > 100:
                return jsonify({'error': 'Number of reviews must be between 1 and 100'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid number of reviews'}), 400
        
        print(f"🎲 Scraping {num_reviews} reviews from: {url[:60]}...")
        
        result = scraper.get_random_reviews(url, num_reviews=num_reviews)
        
        print(f"✅ Successfully scraped {result.get('review_stats', {}).get('selected_reviews_count', 0)} reviews")
        
        return jsonify(result)
        
    except ValueError as e:
        error_msg = str(e)
        print(f"❌ Validation error: {error_msg}")
        return jsonify({'error': error_msg}), 400
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/extract-data-id', methods=['POST'])
def extract_data_id():
    """Extract data_id from Google Maps URL"""
    try:
        if not scraper:
            return jsonify({'error': 'Scraper not available'}), 500
        
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Extract data_id from URL
        data_id = scraper.extract_data_id_from_url(url)
        
        if not data_id:
            return jsonify({'error': 'Could not extract data_id from URL'}), 400
        
        # Validate the extracted data_id
        if not scraper.validate_data_id(data_id):
            return jsonify({'error': 'Invalid data_id format'}), 400
        
        return jsonify({
            'data_id': data_id,
            'url': url,
            'valid': True
        })
        
    except Exception as e:
        error_msg = f"Error extracting data_id: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({'error': error_msg}), 500

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify server is working"""
    return jsonify({
        'message': 'Server is working!',
        'endpoints': {
            'health': '/health',
            'scrape': '/scrape (POST)',
            'extract_data_id': '/extract-data-id (POST)',
            'test': '/test'
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def main():
    """Run the Flask server"""
    print("🚀 Starting Restaurant Review Scraper Server")
    print("=" * 50)
    
    if not scraper:
        print("⚠️  Warning: Scraper initialization failed!")
        print("   Make sure your .env file exists with a valid DOG_KEY")
        print("   The server will run but scraping will not work.")
    else:
        print("✅ Scraper ready")
    
    if not ai_system_available:
        print("⚠️  Warning: AI generation system not available!")
        print("   Make sure your .env file has OPENAI_API_KEY and COHERE_API_KEY")
        print("   Chat functionality will work but with limited responses.")
    else:
        print("✅ AI generation system ready")
    
    print("\n🌐 Server will be available at:")
    print("   http://localhost:5000")
    print("\n📋 Available endpoints:")
    print("   GET  /health - Health check")
    print("   POST /chat - Chat about restaurants (NEW!)")
    print("   POST /scrape - Scrape reviews (legacy)")
    print("   POST /extract-data-id - Extract data ID from URL")
    print("   GET  /test - Test endpoint")
    
    print("\n💡 Usage:")
    print("   1. Install the Chrome extension")
    print("   2. Navigate to a restaurant on Google Maps")
    print("   3. Click the extension icon")
    print("   4. Ask questions about the restaurant!")
    print("   5. Get intelligent answers based on reviews")
    
    print("\n🛑 To stop the server, press Ctrl+C")
    print("=" * 50)
    
    try:
        app.run(host='localhost', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

if __name__ == '__main__':
    main() 
