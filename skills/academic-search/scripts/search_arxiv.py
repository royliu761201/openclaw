#!/usr/bin/env python3
import argparse
import json
import arxiv
import os

def search_arxiv_papers(query, max_results=5, sort_by="relevance"):
    try:
        import requests
        session = requests.Session()
        
        # arXiV wrapper uses properties or private session. We patch the underlying get/post.
        class TimeoutAdapter(requests.adapters.HTTPAdapter):
            def send(self, *args, **kwargs):
                kwargs['timeout'] = 15.0
                return super().send(*args, **kwargs)
                
        session.mount('https://', TimeoutAdapter())
        session.mount('http://', TimeoutAdapter())
        session.headers.update({'User-Agent': 'OpenClaw Radar V3'})

        client = arxiv.Client(
            page_size=max_results,
            delay_seconds=3.0,
            num_retries=2
        )
        client._session = session
        
        sort_criterion = arxiv.SortCriterion.SubmittedDate if sort_by.lower() == "date" else arxiv.SortCriterion.Relevance
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_criterion
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
    search_parser.add_argument('--sort_by', type=str, choices=['relevance', 'date'], default='relevance')
    
    args = parser.parse_args()
    
    if args.command == 'search':
        search_arxiv_papers(args.query, args.max_results, args.sort_by)
    else:
        # Default behavior if query argument is present
        if hasattr(args, 'query') and args.query:
             search_arxiv_papers(args.query, args.max_results, getattr(args, 'sort_by', 'relevance'))
        else:
             parser.print_help()
