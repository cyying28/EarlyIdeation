import os
import openai
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMInterface:
    def __init__(self, api_key=None, model="gpt-4o-mini"):
        # Use provided API key or get from environment
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY not found in environment variables")
            
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        
    def rag_sys_prompt(self, restaurant: str, reviews: list[dict], avg_stars: float, avg_food_stars: float, avg_atmosphere_stars: float, avg_service_stars: float):
        system_prompt = f"""
        You are an experienced food review analysis expert and will be provided with a list of relevant reviews to the user_prompt. Synthesize
        the reviews and provide details on your explanations. Rely entirely on the data below to conduct your analysis.
        
        Restaurant: {restaurant}
        Average Overall Rating: {avg_stars:.2f} / 5 stars
        Average Food Rating: {f"{avg_food_stars:.2f} / 5 stars" if avg_food_stars is not None else "No specific food ratings available"}
        Average Atmosphere Rating: {f"{avg_atmosphere_stars:.2f} / 5 stars" if avg_atmosphere_stars is not None else "No specific atmosphere ratings available"}
        Average Service Rating: {f"{avg_service_stars:.2f} / 5 stars" if avg_service_stars is not None else "No specific service ratings available"}
        
        Relevant Reviews: {''.join(f'\n\n"{review["snippet"]}"' for review in reviews)}
        
        Based on the above reviews and ratings, provide a comprehensive analysis that answers the user's question. 
        Be specific and cite examples from the reviews when possible.
        """
        return system_prompt

    def food_review_prompt(self, rag_sys_prompt: str, user_prompt: str):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": rag_sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating AI response: {str(e)}"

# if __name__ == "__main__":
#     system_prompt = "You are a helpful assistant that speaks politely and provides concise answers."
#     user_prompt = "Can you explain what a system prompt is?"
    
#     answer = chat_with_system_prompt(system_prompt, user_prompt)
#     print("Assistant:", answer)

# def generate_answer(query):
#     contexts = retrieve_similar_documents(query)
#     prompt = (
#         "Use the following context to answer the question.\n\n"
#         + "\n\n".join(contexts)
#         + f"\n\nQuestion: {query}\nAnswer:"
#     )

#     response = openai.ChatCompletion.create(
#         model="gpt-4",  # or gpt-3.5-turbo
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.7,
#     )
#     return response['choices'][0]['message']['content']