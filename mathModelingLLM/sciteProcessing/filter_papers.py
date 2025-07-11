"""
Filter mathematical modeling papers to remove those with NULL abstracts
"""

import json

def filter_papers():
    """Filter papers to remove those with NULL abstracts."""
    
    # Load the original JSON file
    with open('mathematical_modeling_papers.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    filtered_data = {}
    total_original = 0
    total_filtered = 0
    
    # Filter each query
    for query, query_data in data.items():
        papers = query_data.get('papers', [])
        original_count = len(papers)
        total_original += original_count
        
        # Filter out papers with NULL or empty abstracts
        filtered_papers = [
            paper for paper in papers 
            if paper.get('abstract') and paper['abstract'].strip() and paper['abstract'] != 'null'
        ]
        
        filtered_count = len(filtered_papers)
        total_filtered += filtered_count
        
        print(f"{query}: {original_count} → {filtered_count} papers (removed {original_count - filtered_count})")
        
        # Create filtered query data
        filtered_data[query] = {
            'query': query,
            'count': filtered_count,
            'papers': filtered_papers
        }
    
    # Save filtered data
    output_file = 'mathematical_modeling_papers_filtered.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print("FILTERING SUMMARY")
    print(f"{'='*50}")
    print(f"Original papers: {total_original}")
    print(f"Papers with abstracts: {total_filtered}")
    print(f"Papers removed: {total_original - total_filtered}")
    print(f"Retention rate: {total_filtered/total_original*100:.1f}%")
    print(f"Filtered data saved to: {output_file}")

if __name__ == "__main__":
    filter_papers() 