"""
Analyze mathematical modeling papers JSON file
"""

import json

def analyze_papers():
    """Analyze the papers JSON file."""
    
    # Load the JSON file
    with open('mathematical_modeling_papers.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_papers = 0
    papers_with_abstracts = 0
    papers_with_dois = 0
    papers_with_citations = 0
    
    # Analyze each query
    for query, query_data in data.items():
        papers = query_data.get('papers', [])
        query_count = len(papers)
        total_papers += query_count
        
        print(f"\n{query}: {query_count} papers")
        
        # Count papers with abstracts
        abstracts_count = sum(1 for paper in papers if paper.get('abstract') and paper['abstract'].strip())
        papers_with_abstracts += abstracts_count
        print(f"  Papers with abstracts: {abstracts_count}/{query_count}")
        
        # Count papers with DOIs
        dois_count = sum(1 for paper in papers if paper.get('doi'))
        papers_with_dois += dois_count
        print(f"  Papers with DOIs: {dois_count}/{query_count}")
        
        # Count papers with citations
        citations_count = sum(1 for paper in papers if paper.get('citations', {}).get('total', 0) > 0)
        papers_with_citations += citations_count
        print(f"  Papers with citations: {citations_count}/{query_count}")
    
    # Overall summary
    print(f"\n{'='*50}")
    print("OVERALL SUMMARY")
    print(f"{'='*50}")
    print(f"Total papers: {total_papers}")
    print(f"Papers with abstracts: {papers_with_abstracts}/{total_papers} ({papers_with_abstracts/total_papers*100:.1f}%)")
    print(f"Papers with DOIs: {papers_with_dois}/{total_papers} ({papers_with_dois/total_papers*100:.1f}%)")
    print(f"Papers with citations: {papers_with_citations}/{total_papers} ({papers_with_citations/total_papers*100:.1f}%)")

if __name__ == "__main__":
    analyze_papers() 