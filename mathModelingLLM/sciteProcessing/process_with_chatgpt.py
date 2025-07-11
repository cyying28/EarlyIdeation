"""
Process papers through ChatGPT to extract problem and solution from abstracts
"""

import json
import time
import os
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_problem_solution(abstract: str, query: str) -> Dict[str, str]:
    """
    Use ChatGPT to extract problem and solution from abstract.
    
    Args:
        abstract: The paper's abstract
        query: The search query that found this paper
        
    Returns:
        Dictionary with 'problem' and 'solution' fields
    """

    prompt = f"""
    Based on the following abstract from a research paper about "{query}", extract:
    1. The problem being addressed (1-3 sentences)
    2. The solution proposed (1-3 sentences)

    Abstract: {abstract}

    Please respond with ONLY a JSON object in this exact format:
    {{
        "problem": "1-3 sentence description of the problem",
        "solution": "1-3 sentence description of the solution"
    }}
    """

    try:
        response = client.chat.completions.create(model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts problem and solution from research abstracts. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=500)

        # Extract the JSON response
        content = response.choices[0].message.content.strip()

        # Try to parse the JSON response
        try:
            result = json.loads(content)
            return {
                'problem': result.get('problem', ''),
                'solution': result.get('solution', '')
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract manually
            print(f"Warning: Could not parse JSON response: {content}")
            return {
                'problem': 'Could not extract problem',
                'solution': 'Could not extract solution'
            }

    except Exception as e:
        print(f"Error calling ChatGPT: {e}")
        return {
            'problem': 'Error extracting problem',
            'solution': 'Error extracting solution'
        }

def process_papers():
    """Process all papers through ChatGPT to extract problem and solution."""

    # Load the filtered papers
    with open('mathematical_modeling_papers_filtered.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    processed_papers = []
    total_papers = 0

    # Count total papers first
    for query_data in data.values():
        total_papers += len(query_data.get('papers', []))

    print(f"Processing {total_papers} papers through ChatGPT...")

    # Process each paper
    paper_count = 0
    for query, query_data in data.items():
        papers = query_data.get('papers', [])

        print(f"\nProcessing {len(papers)} papers for query: {query}")

        for paper in papers:
            paper_count += 1
            print(f"  [{paper_count}/{total_papers}] Processing: {paper.get('title', 'No title')[:50]}...")

            # Extract problem and solution from abstract
            abstract = paper.get('abstract', '')
            problem_solution = extract_problem_solution(abstract, query)

            # Create processed paper entry
            processed_paper = {
                'query': query,
                'title': paper.get('title', ''),
                'doi': paper.get('doi', ''),
                'problem': problem_solution['problem'],
                'solution': problem_solution['solution'],
                'year': paper.get('year'),
                'journal': paper.get('journal', ''),
                'citations': paper.get('citations', {})
            }

            processed_papers.append(processed_paper)

            # Rate limiting - wait between API calls
            time.sleep(1)

    # Save processed papers
    output_file = 'processed_papers_with_chatgpt.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_papers, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print("PROCESSING COMPLETE")
    print(f"{'='*50}")
    print(f"Total papers processed: {len(processed_papers)}")
    print(f"Output saved to: {output_file}")

    # Show sample of processed data
    if processed_papers:
        print(f"\nSample processed paper:")
        sample = processed_papers[0]
        print(f"Query: {sample['query']}")
        print(f"Title: {sample['title']}")
        print(f"Problem: {sample['problem']}")
        print(f"Solution: {sample['solution']}")
        print(f"Citations: {sample['citations']}")

if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your_api_key_here'")
        exit(1)

    process_papers() 