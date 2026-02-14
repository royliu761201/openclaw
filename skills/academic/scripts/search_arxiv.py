import argparse
import json
import arxiv
import os

def search_arxiv_papers(query, max_results=5):
    try:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        results = []
        for result in search.results():
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

def download_paper(paper_id, filename=None):
    try:
        # Arxiv library download
        paper = next(arxiv.Search(id_list=[paper_id]).results())
        
        # Ensure workspace/papers exists
        output_dir = os.path.join(os.getcwd(), 'workspace', 'papers')
        os.makedirs(output_dir, exist_ok=True)
        
        if not filename:
            filename = f"{paper_id}.pdf"
            
        path = paper.download_pdf(dirpath=output_dir, filename=filename)
        print(json.dumps({"status": "success", "path": path}))
        
    except Exception as e:
         print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ArXiv Tool')
    subparsers = parser.add_subparsers(dest='command')
    
    search_parser = subparsers.add_parser('search')
    search_parser.add_argument('--query', required=True)
    search_parser.add_argument('--max_results', type=int, default=5)
    
    download_parser = subparsers.add_parser('download')
    download_parser.add_argument('--id', required=True)
    download_parser.add_argument('--filename')
    
    args = parser.parse_args()
    
    if args.command == 'search':
        search_arxiv_papers(args.query, args.max_results)
    elif args.command == 'download':
        download_paper(args.id, args.filename)
