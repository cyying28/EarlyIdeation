"""
Process papers through ChatGPT to extract problem and solution from abstracts
"""

import json
import time
import os
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    You are an expert in mathematical modeling and research methodology. Based on the following abstract from a research paper about "{query}", extract:

    1. PROBLEM: Describe the mathematical modeling challenge or research problem being addressed. Include:
       - The specific mathematical/computational challenge
       - Why existing methods are insufficient
       - The practical or theoretical gap being filled
       - Any constraints or limitations mentioned

    2. SOLUTION: Describe the mathematical approach or methodology proposed. Include:
       - The specific mathematical technique or algorithm used 
       - Step-by-step process or key mathematical operations
       - How it addresses the identified problem
       - Key innovations or improvements over existing methods
       - The mathematical framework or theoretical foundation

    Abstract: {abstract}

    Guidelines:
    - Be specific about mathematical concepts and techniques
    - Use precise, technical language suitable for ML training
    - Focus on the mathematical modeling aspects
    - Ensure the problem-solution pair is coherent and complete
    - Write in a way that would help train an LLM to recommend mathematical solutions
    - AVOID vague descriptions like "broadly applicable algorithm" - explain WHAT the algorithm actually does
    - Include specific mathematical operations, formulas, or computational steps when mentioned
    - Be concrete about the methodology rather than just listing applications

    Please respond with ONLY a JSON object in this exact format:
    {{
        "problem": "Detailed description of the mathematical modeling challenge (2-4 sentences)",
        "solution": "Detailed description of the mathematical approach and methodology (2-4 sentences)"
    }}
    """

    try:
        response = client.chat.completions.create(model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts problem and solution from research abstracts. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=800)

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

def process_paper_batch(papers_batch: List[Dict], query: str) -> List[Dict]:
    """Process a batch of papers concurrently."""
    results = []
    
    def process_single_paper(paper):
        try:
            abstract = paper.get('abstract', '')
            problem_solution = extract_problem_solution(abstract, query)
            
            return {
                'query': query,
                'title': paper.get('title', ''),
                'doi': paper.get('doi', ''),
                'problem': problem_solution['problem'],
                'solution': problem_solution['solution'],
                'year': paper.get('year'),
                'journal': paper.get('journal', ''),
                'citations': paper.get('citations', {})
            }
        except Exception as e:
            print(f"Error processing paper {paper.get('title', 'Unknown')}: {e}")
            return None
    
    # Process papers in parallel with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all papers in the batch
        future_to_paper = {executor.submit(process_single_paper, paper): paper for paper in papers_batch}
        
        # Collect results as they complete
        for future in as_completed(future_to_paper):
            result = future.result()
            if result:
                results.append(result)
    
    return results

def process_papers():
    """Process all papers through ChatGPT to extract problem and solution."""

    # Load the filtered papers
    with open('jsons/mathematical_modeling_papers_filtered.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    processed_papers = []
    total_papers = 0

    # Count total papers first
    for query_data in data.values():
        total_papers += len(query_data.get('papers', []))

    print(f"Processing {total_papers} papers through ChatGPT...")

    # Process papers in batches for each query
    paper_count = 0
    for query, query_data in data.items():
        papers = query_data.get('papers', [])
        
        if not papers:
            continue

        print(f"\nProcessing {len(papers)} papers for query: {query}")
        
        # Process papers in parallel batches
        batch_size = 5  # Process 5 papers at a time
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(papers) + batch_size - 1) // batch_size
            
            print(f"  Batch {batch_num}/{total_batches} ({len(batch)} papers)")
            
            # Process batch in parallel
            batch_results = process_paper_batch(batch, query)
            processed_papers.extend(batch_results)
            
            paper_count += len(batch_results)
            print(f"  Completed {paper_count}/{total_papers} papers")
            
            # Small delay between batches to be respectful to API
            time.sleep(0.5)

    # Save processed papers
    output_file = 'processed_papers_with_chatgpt_2.json'
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