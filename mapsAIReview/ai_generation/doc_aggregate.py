import json
import os

class DocAggregate:
    @staticmethod
    def extract_reviews_json(json_file_path: str):
        """
        From JSON file, extracts the metadata about the restaurant and outputs a new dict with the reviews in list format (index is their ID)
        """
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")
            
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")

        # Extract restaurant metadata
        location_details = data.get("locationDetails", {})
        restaurant_name = location_details.get("title", "Unknown Restaurant")
        restaurant_address = location_details.get("address", "Unknown Address")
        overall_rating = location_details.get("rating", None)
        
        metadata = {
            "name": restaurant_name,
            "address": restaurant_address,
            "overall rating": overall_rating
        }
        
        reviews = data.get("reviews", [])
        if not reviews:
            print("Warning: No reviews found in the JSON file")

        formatted_reviews = []
        # Reviews maintain their identity through their index in the JSON
        for idx, review in enumerate(reviews, 1):
            snippet = review.get("snippet", "").strip()
            if snippet:  # Only include reviews with actual content
                doc_dict = {
                    "id": idx,
                    "address": restaurant_address,
                    "snippet": snippet,
                    "details": review.get("details", {})
                }
                formatted_reviews.append(doc_dict)

        print(f"Extracted metadata for: {restaurant_name}")
        print(f"Found {len(formatted_reviews)} reviews with content")
        
        return metadata, formatted_reviews
    
    @staticmethod
    def avg_review_rating(category: str, docs: list):
        """
        Calculates the average of a numerical column (e.g., rating) from the output of RAG
        If the value is missing or not a number, it is skipped.
        """
        if not docs:
            return None
            
        total = 0
        count = 0
        
        for doc in docs:
            details = doc.get("details", {})
            col_val = details.get(category, None)
            
            if isinstance(col_val, (int, float)) and col_val > 0:
                total += col_val
                count += 1

        if count == 0:
            return None
            
        avg = total / count
        print(f"Average {category} rating: {avg:.2f} (from {count} reviews)")
        return avg

    # # Example usage:
    # if __name__ == "__main__":
    #     file_path = "pizza_luce_reviews.json"  # Update with your actual file name
    #     restaurant, reviews = extract_restaurant_and_reviews(file_path)

    #     print(f"Restaurant: {restaurant}\n")
    #     print("Reviews:")
    #     for review in reviews:
    #         print(review)