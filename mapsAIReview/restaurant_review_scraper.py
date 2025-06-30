import requests
import json
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
import time
import random
import re

class RestaurantReviewScraper:
    def __init__(self):
        """Initialize the scraper with API key from environment variables."""
        load_dotenv()
        self.api_key = os.getenv('DOG_KEY')
        if not self.api_key:
            raise ValueError("DOG_KEY not found in environment variables. Please check your .env file.")
        
        self.base_url = "https://api.scrapingdog.com/google_maps/reviews"
        self.session = requests.Session()
    
    def extract_data_id_from_url(self, url: str) -> str:
        """
        Extract data_id from a Google Maps URL.
        
        Args:
            url: Google Maps URL
            
        Returns:
            data_id string or None if not found
        """
        # Look for pattern like: 1s0x89c25090129c363d:0x40c6a5770d25022b
        pattern = r'1s(0x[a-fA-F0-9]+:0x[a-fA-F0-9]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        
        # Alternative pattern in data= parameter
        pattern2 = r'data=.*?1s(0x[a-fA-F0-9]+:0x[a-fA-F0-9]+)'
        match2 = re.search(pattern2, url)
        if match2:
            return match2.group(1)
        
        return None
    
    def validate_data_id(self, data_id: str) -> bool:
        """
        Validate if a data_id looks correct.
        
        Args:
            data_id: The data_id to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not data_id:
            return False
        
        # Should be in format: 0x[hex]:[hex]
        pattern = r'^0x[a-fA-F0-9]+:0x[a-fA-F0-9]+$'
        return bool(re.match(pattern, data_id))
    
    def parse_input(self, input_str: str) -> str:
        """
        Parse input string - can be URL or data_id.
        
        Args:
            input_str: Google Maps URL or data_id
            
        Returns:
            data_id string or raises ValueError if invalid
        """
        input_str = input_str.strip()
        
        if 'google.com/maps' in input_str:
            print(f"🔍 Extracting data_id from URL...")
            data_id = self.extract_data_id_from_url(input_str)
            if not data_id or not self.validate_data_id(data_id):
                raise ValueError("Could not extract valid data_id from URL")
            print(f"✅ Found data_id: {data_id}")
            return data_id
        else:
            if not self.validate_data_id(input_str):
                raise ValueError(f"Invalid data_id format: {input_str}")
            return input_str
    
    def scrape_reviews(self, data_id: str, language: str = "en", max_pages: Optional[int] = None) -> Dict:
        """
        Scrape reviews for a given restaurant data_id.
        
        Args:
            data_id: Google Maps data ID (e.g., "0x89c25090129c363d:0x40c6a5770d25022b")
            language: Language code for reviews (default: "en")
            max_pages: Maximum number of pages to scrape (None for all pages)
        
        Returns:
            Dictionary containing all scraped review data
        """
        all_reviews = []
        location_details = None
        topics = None
        next_page_token = None
        page_count = 0
        
        print(f"Starting to scrape reviews for data_id: {data_id}")
        
        while True:
            # Prepare parameters
            params = {
                "api_key": self.api_key,
                "data_id": data_id,
                "language": language
            }
            
            # Add next page token if available
            if next_page_token:
                params["next_page_token"] = next_page_token
            
            try:
                print(f"Fetching page {page_count + 1}...")
                response = self.session.get(self.base_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Store location details and topics from first page
                    if page_count == 0:
                        location_details = data.get('locationDetails', {})
                        topics = data.get('topics', [])
                        print(f"Restaurant: {location_details.get('title', 'Unknown')}")
                        print(f"Rating: {location_details.get('rating', 'N/A')} ({location_details.get('reviews', 0)} reviews)")
                    
                    # Add reviews from current page
                    page_reviews = data.get('reviews_results', [])
                    all_reviews.extend(page_reviews)
                    print(f"Collected {len(page_reviews)} reviews from page {page_count + 1}")
                    
                    # Check for pagination
                    pagination = data.get('pagination', {})
                    next_page_token = pagination.get('next_page_token')
                    
                    page_count += 1
                    
                    # Check if we should continue
                    if not next_page_token:
                        print("No more pages available.")
                        break
                    
                    if max_pages and page_count >= max_pages:
                        print(f"Reached maximum page limit ({max_pages})")
                        break
                    
                    # Add a small delay to be respectful to the API
                    time.sleep(1)
                    
                else:
                    print(f"Request failed with status code: {response.status_code}")
                    print(f"Response: {response.text}")
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                break
        
        print(f"Total reviews collected: {len(all_reviews)} from {page_count} pages")
        
        return {
            "locationDetails": location_details,
            "topics": topics,
            "reviews_results": all_reviews,
            "total_reviews": len(all_reviews),
            "pages_scraped": page_count
        }
    
    def get_random_reviews(self, input_str: str, num_reviews: int = 50, language: str = "en") -> Dict:
        """
        Get a specified number of random reviews for a restaurant.
        
        Args:
            input_str: Google Maps URL or data_id
            num_reviews: Number of random reviews to return (default: 50)
            language: Language code for reviews (default: "en")
        
        Returns:
            Dictionary containing random reviews and location details
        """
        # Parse input to get data_id
        data_id = self.parse_input(input_str)
        
        print(f"🎲 Getting {num_reviews} random reviews for restaurant...")
        
        # Calculate how many pages we likely need (assuming ~8-10 reviews per page)
        estimated_pages_needed = max(3, (num_reviews // 8) + 2)
        
        # Scrape enough reviews to have a good selection
        print(f"📄 Scraping up to {estimated_pages_needed} pages to gather reviews...")
        data = self.scrape_reviews(data_id, max_pages=estimated_pages_needed, language=language)
        
        all_reviews = data.get('reviews_results', [])
        
        if len(all_reviews) < num_reviews:
            print(f"⚠️  Only found {len(all_reviews)} reviews, returning all available reviews")
            selected_reviews = all_reviews
        else:
            # Randomly sample the requested number of reviews
            print(f"🎯 Randomly selecting {num_reviews} reviews from {len(all_reviews)} available")
            selected_reviews = random.sample(all_reviews, num_reviews)
        
        # Create simplified review structure
        simplified_reviews = []
        for review in selected_reviews:
            simplified_review = {
                "snippet": review.get('snippet', ''),
                "details": review.get('details', {})
            }
            simplified_reviews.append(simplified_review)
        
        # Create clean output structure
        result = {
            "locationDetails": data.get('locationDetails', {}),
            "review_stats": {
                "total_available_reviews": len(all_reviews),
                "selected_reviews_count": len(selected_reviews),
                "sampling_method": "random",
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "reviews": simplified_reviews
        }
        
        print(f"✅ Successfully selected {len(selected_reviews)} random reviews")
        return result
    
    def save_to_file(self, data: Dict, filename: str = None) -> str:
        """
        Save scraped data to a JSON file.
        
        Args:
            data: Dictionary containing scraped data
            filename: Optional filename (auto-generated if not provided)
        
        Returns:
            Filename of saved file
        """
        if not filename:
            restaurant_name = data.get('locationDetails', {}).get('title', 'restaurant')
            # Clean filename
            restaurant_name = "".join(c for c in restaurant_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            restaurant_name = restaurant_name.replace(' ', '_')
            filename = f"{restaurant_name}_reviews.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to: {filename}")
        return filename
    
    def get_review_summary(self, data: Dict) -> Dict:
        """
        Generate a summary of the scraped reviews.
        
        Args:
            data: Dictionary containing scraped data
        
        Returns:
            Dictionary with review summary statistics
        """
        reviews = data.get('reviews_results', [])
        if not reviews:
            return {"error": "No reviews found"}
        
        # Rating distribution
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_likes = 0
        
        for review in reviews:
            rating = review.get('rating', 0)
            if rating in rating_counts:
                rating_counts[rating] += 1
            total_likes += review.get('likes', 0)
        
        # Calculate average rating
        total_ratings = sum(rating * count for rating, count in rating_counts.items())
        total_reviews = len(reviews)
        avg_rating = total_ratings / total_reviews if total_reviews > 0 else 0
        
        return {
            "total_reviews": total_reviews,
            "average_rating": round(avg_rating, 2),
            "rating_distribution": rating_counts,
            "total_likes": total_likes,
            "reviews_with_images": len([r for r in reviews if r.get('images')]),
            "reviews_with_response": len([r for r in reviews if r.get('response', {}).get('response_from_owner_string')])
        }

def main():
    """Main function to demonstrate usage."""
    scraper = RestaurantReviewScraper()
    
    # Example data_id from your example.json (Statue of Liberty)
    # Replace with actual restaurant data_id
    data_id = "0x89c25090129c363d:0x40c6a5770d25022b"
    
    print("Restaurant Review Scraper")
    print("=" * 40)
    
    # Option to input custom URL or data_id
    print(f"\n📍 You can enter either:")
    print("   • Full Google Maps URL (from browser address bar)")
    print("   • data_id (like: 0x89c25090129c363d:0x40c6a5770d25022b)")
    
    user_input = input(f"\n🔗 Enter URL/data_id (or press Enter to use example): ").strip()
    if user_input:
        try:
            data_id = scraper.parse_input(user_input)
        except ValueError as e:
            print(f"❌ Error: {e}")
            return
    
    # Choose scraping mode
    print("\nChoose scraping mode:")
    print("1. 🎲 Get random reviews (default: 50)")
    print("2. 📄 Scrape all/specific pages")
    
    mode = input("Enter choice (1 or 2): ").strip()
    
    try:
        if mode == "1":
            # Random reviews mode
            num_reviews_input = input("How many random reviews? (default: 50): ").strip()
            num_reviews = 50
            if num_reviews_input.isdigit():
                num_reviews = int(num_reviews_input)
            
            # Get random reviews
            data = scraper.get_random_reviews(user_input if user_input else data_id, num_reviews=num_reviews)
            
            # Save to file with specific naming
            restaurant_name = data.get('locationDetails', {}).get('title', 'restaurant')
            restaurant_name = "".join(c for c in restaurant_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            restaurant_name = restaurant_name.replace(' ', '_')
            filename = f"{restaurant_name}_random_{num_reviews}_reviews.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved {data.get('review_stats', {}).get('selected_reviews_count', 0)} random reviews to: {filename}")
            
        else:
            # Regular scraping mode
            max_pages_input = input("Enter maximum pages to scrape (or press Enter for all pages): ").strip()
            max_pages = None
            if max_pages_input.isdigit():
                max_pages = int(max_pages_input)
            
            # Scrape reviews
            data = scraper.scrape_reviews(data_id, max_pages=max_pages)
            
            # Save to file
            filename = scraper.save_to_file(data)
            
            # Display summary
            summary = scraper.get_review_summary(data)
            print("\nReview Summary:")
            print("=" * 20)
            for key, value in summary.items():
                if key == "rating_distribution":
                    print(f"{key}:")
                    for rating, count in value.items():
                        print(f"  {rating} stars: {count} reviews")
                else:
                    print(f"{key}: {value}")
            
            print(f"\nData saved to: {filename}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 
