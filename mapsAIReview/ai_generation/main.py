import os
from dotenv import load_dotenv
from doc_aggregate import DocAggregate
from llm_interface import LLMInterface
from rag import RagTools

# Load environment variables from .env file
load_dotenv()

def run_ai_review(json_path: str, query: str):
    # Get API keys from environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    cohere_api_key = os.getenv("COHERE_API_KEY")
    
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    if not cohere_api_key:
        raise ValueError("COHERE_API_KEY not found in environment variables")
    
    # Parse Phase
    restaurant_data, review_docs = DocAggregate.extract_reviews_json(json_path)
    
    # RAG Phase
    print("Processing reviews...")
    print(f"Found {len(review_docs)} reviews")
    
    rag_db = RagTools("restaurants", cohere_api_key)
    rag_db.create_collection()
    rag_db.upload_documents(review_docs)
    relevant_reviews = rag_db.retrieve_similar_reviews(restaurant_data["address"], query)
    
    # LLM Phase
    llm = LLMInterface(openai_api_key)
    avg_stars = restaurant_data["overall rating"]
    avg_food_stars = DocAggregate.avg_review_rating("food", relevant_reviews)
    avg_service_stars = DocAggregate.avg_review_rating("service", relevant_reviews)
    avg_atmosphere_stars = DocAggregate.avg_review_rating("atmosphere", relevant_reviews)
    
    sys_prompt = llm.rag_sys_prompt(restaurant_data["name"], relevant_reviews, avg_stars, avg_food_stars, avg_service_stars, avg_atmosphere_stars)
    print(f"Found {len(relevant_reviews)} relevant reviews for your query")
    response = llm.food_review_prompt(sys_prompt, query)
    return response

if __name__ == "__main__":
    # Example usage - update path to your actual JSON file
    json_file = "/Users/curtisying/Desktop/Coding/mapsAIReview/Pizza_Lucé_Eden_Prairie_random_20_reviews.json"
    query = "How is the pizza?"
    
    try:
        result = run_ai_review(json_file, query)
        print("\n" + "="*50)
        print("AI ANALYSIS:")
        print("="*50)
        print(result)
    except Exception as e:
        print(f"Error: {e}")