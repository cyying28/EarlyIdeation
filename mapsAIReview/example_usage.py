#!/usr/bin/env python3
"""
Example usage of the Restaurant Review Scraper.
This script demonstrates how to use the scraper programmatically.
"""

from restaurant_review_scraper import RestaurantReviewScraper

def scrape_restaurant_reviews(data_id: str, max_pages: int = None):
    """
    Example function to scrape restaurant reviews.
    
    Args:
        data_id: Google Maps data ID for the restaurant
        max_pages: Maximum number of pages to scrape (None for all)
    """
    try:
        # Initialize the scraper
        scraper = RestaurantReviewScraper()
        
        # Scrape reviews
        print(f"Scraping reviews for data_id: {data_id}")
        data = scraper.scrape_reviews(data_id, max_pages=max_pages)
        
        # Get summary
        summary = scraper.get_review_summary(data)
        
        # Save to file
        filename = scraper.save_to_file(data)
        
        # Print results
        print(f"\n✅ Successfully scraped {summary['total_reviews']} reviews")
        print(f"📊 Average rating: {summary['average_rating']}/5")
        print(f"💾 Data saved to: {filename}")
        
        return data, filename
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        return None, None

def main():
    """Main function with examples."""
    print("🍽️  Restaurant Review Scraper - Example Usage")
    print("=" * 50)
    
    # Example 1: Scrape all reviews for a restaurant
    # Replace with actual restaurant data_id
    restaurant_data_id = "0x89c25090129c363d:0x40c6a5770d25022b"  # Example from your JSON
    
    print("\n📝 Example 1: Scraping first 2 pages only")
    data1, file1 = scrape_restaurant_reviews(restaurant_data_id, max_pages=2)
    
    # Example 2: You can also scrape all reviews (remove max_pages parameter)
    # print("\n📝 Example 2: Scraping ALL reviews")
    # data2, file2 = scrape_restaurant_reviews(restaurant_data_id)
    
    if data1:
        print("\n🎯 Additional analysis:")
        reviews = data1.get('reviews_results', [])
        
        # Find most liked review
        most_liked = max(reviews, key=lambda x: x.get('likes', 0), default=None)
        if most_liked:
            print(f"👍 Most liked review: {most_liked.get('likes', 0)} likes")
            print(f"   User: {most_liked.get('user', {}).get('name', 'Unknown')}")
            print(f"   Rating: {most_liked.get('rating', 'N/A')}/5")
        
        # Find recent reviews
        recent_reviews = [r for r in reviews if 'week' in r.get('date', '').lower()]
        print(f"🕒 Recent reviews (this week): {len(recent_reviews)}")

if __name__ == "__main__":
    main() 