#!/usr/bin/env python3
import argparse
import json
import arxiv
import os

def search_arxiv_papers(query, max_results=5):
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        results = []
        for result in client.results(search):
            paper = {
                'id': result.entry_id.split('/')[-1],
                'title': result.title,
                'summary': result.summary.replace('\n', ' '),
                'published': str(result.published),
                'authors': [a.name for a in result.authors],
                'pdf_url': result.pdf_url
            }
            results.append(paper)
        
        print(json.dumps(results, indent=2))
            
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ArXiv Tool')
    subparsers = parser.add_subparsers(dest='command')
    
    search_parser = subparsers.add_parser('search')
    search_parser.add_argument('--query', required=True)
    search_parser.add_argument('--max_results', type=int, default=5)
    
    args = parser.parse_args()
    
    if args.command == 'search':
        search_arxiv_papers(args.query, args.max_results)
    else:
        # Default behavior if query argument is present (backwards compatibility or simpler usage)
        if hasattr(args, 'query') and args.query:
             search_arxiv_papers(args.query, args.max_results)
        else:
             parser.print_help()
