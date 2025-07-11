"""
Scite Paper Collector - Mathematical Modeling Queries

Collects top 10 scite results for mathematical modeling queries and outputs to JSON.
"""

import os
import json
import time
from typing import List, Dict, Optional, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class SciteClient:
    """Client for interacting with the scite.ai API."""
    
    BASE_URL = "https://api.scite.ai"
    
    def __init__(self, api_token: Optional[str] = None, rate_limit_delay: float = 0.1):
        self.api_token = api_token or os.getenv("SCITE_BEARER_TOKEN")
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        
        if self.api_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10)
        )
        def _request():
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        
        result = _request()
        time.sleep(self.rate_limit_delay)
        return result
    
    def get_tally(self, doi: str, use_view: bool = True) -> Dict[str, Any]:
        """Get smart citation tally for a DOI."""
        params = {"use_view": use_view}
        return self._make_request("GET", f"/tallies/{doi}", params=params)
    
    def search(self, 
               term: str = "",
               mode: str = "all",
               limit: int = 10,
               offset: int = 0,
               format: str = "json",
               **kwargs) -> Dict[str, Any]:
        """Search scite database."""
        if limit > 10000:
            raise ValueError("Maximum 10,000 results allowed per request")
        
        params = {
            "term": term,
            "mode": mode,
            "limit": limit,
            "offset": offset,
            "format": format,
            **kwargs
        }
        
        return self._make_request("GET", "/search/v2", params=params)


# Mathematical modeling queries
QUERIES = [
    "TOPSIS",
    "GRA",
    "AHP Weights",
    "Entropic Weights", 
    "Pearson Correlation",
    "Granger Causality",
    "Kendall Tau",
    "Divided Differences",
    "ARIMA",
    "ADFuller",
    "F Test",
    "Chi-Squared Test",
    "Exponential Smoothing",
    "Exponential",
    "Sum of Sines Splines",
    "Weighted Moving Average",
    "Bollinger Bands",
    "Markov Chains",
    "Bell Curve",
    "SIR",
    "Logistic/Population",
    "Queue Model",
    "Compound Annual Growth Rate",
    "Economy curve",
    "Monte Carlo Simulation",
    "Graph Theory",
    "Game Theory",
    "Deseasonalization"
]


def extract_paper_metadata(paper_data: Dict[str, Any], client: SciteClient) -> Dict[str, Any]:
    """Extract relevant metadata from a paper result."""
    doi = paper_data.get('doi')
    
    metadata = {
        'title': paper_data.get('title', ''),
        'doi': doi,
        'year': paper_data.get('year'),
        'journal': paper_data.get('journal', ''),
        'abstract': paper_data.get('abstract', ''),
        'keywords': paper_data.get('keywords', []),
        'topics': paper_data.get('topics', []),
        'source': paper_data.get('source', ''),
        'scite_score': paper_data.get('scite_score'),
        'retracted': paper_data.get('retracted', False),
        'editorialNotices': paper_data.get('editorialNotices', []),
        'snippets': paper_data.get('snippets', []),
        'num_snippets': len(paper_data.get('snippets', [])),
        'num_keywords': len(paper_data.get('keywords', [])),
        'num_topics': len(paper_data.get('topics', [])),
        'citations': {}
    }
    
    # Get citation data if DOI is available
    if doi:
        try:
            tally = client.get_tally(doi)
            metadata['citations'] = {
                'total': tally.get('total', 0),
                'supporting': tally.get('supporting', 0),
                'contradicting': tally.get('contradicting', 0),
                'mentioning': tally.get('mentioning', 0),
                'unclassified': tally.get('unclassified', 0),
                'citingPublications': tally.get('citingPublications', 0)
            }
        except Exception as e:
            print(f"Warning: Could not fetch citation data for {doi}: {e}")
            metadata['citations'] = {
                'total': 0,
                'supporting': 0,
                'contradicting': 0,
                'mentioning': 0,
                'unclassified': 0,
                'citingPublications': 0
            }
    
    return metadata


def collect_papers_for_query(query: str, client: SciteClient, limit: int = 10) -> List[Dict[str, Any]]:
    """Collect papers for a specific query."""
    print(f"Searching for: {query}")
    
    try:
        search_results = client.search(
            term=query,
            mode="all",
            limit=limit,
            sort="total_cited",
            sort_order="desc"
        )
        
        papers = []
        hits = search_results.get('hits', [])
        
        print(f"Found {len(hits)} results for '{query}'")
        
        for i, hit in enumerate(hits):
            print(f"  Processing result {i+1}/{len(hits)}: {hit.get('title', 'No title')[:50]}...")
            
            paper_metadata = extract_paper_metadata(hit, client)
            papers.append(paper_metadata)
            
            time.sleep(0.2)
        
        return papers
        
    except Exception as e:
        print(f"Error searching for '{query}': {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Handle RetryError to get the underlying exception
        if hasattr(e, 'last_attempt'):
            last_exception = e.last_attempt.exception()
            print(f"Underlying error: {last_exception}")
            if hasattr(last_exception, 'response'):
                print(f"Response status: {last_exception.response.status_code}")
                print(f"Response text: {last_exception.response.text[:200]}")
        elif hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text[:200]}")
        
        return []


def main():
    """Collect papers for all mathematical modeling queries."""
    print("Scite Paper Collection Script")
    print("=" * 50)
    
    client = SciteClient()
    
    if not client.api_token:
        print("Warning: No API token found. Set SCITE_BEARER_TOKEN environment variable.")
    else:
        print(f"API token found: {client.api_token[:10]}...")
    
    all_results = {}
    
    for i, query in enumerate(QUERIES, 1):
        print(f"\n[{i}/{len(QUERIES)}] Processing query: {query}")
        print("-" * 40)
        
        papers = collect_papers_for_query(query, client)
        
        all_results[query] = {
            'query': query,
            'count': len(papers),
            'papers': papers
        }
        
        print(f"Collected {len(papers)} papers for '{query}'")
        
        if i < len(QUERIES):
            print("Waiting 2 seconds before next query...")
            time.sleep(2)
    
    output_file = "mathematical_modeling_papers.json"
    print(f"\nSaving results to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 50)
    print("COLLECTION SUMMARY")
    print("=" * 50)
    
    total_papers = 0
    for query, data in all_results.items():
        count = data['count']
        total_papers += count
        print(f"{query}: {count} papers")
    
    print(f"\nTotal papers collected: {total_papers}")
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main() 