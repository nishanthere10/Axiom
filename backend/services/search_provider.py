import os
from tavily import TavilyClient

def search_tavily(queries: list[str]) -> list[dict]:
    """
    Executes search queries using Tavily and returns a list of results.
    Each result contains 'title', 'url', and 'raw_content' (if available).
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("WARNING: TAVILY_API_KEY not set. Returning empty results.")
        return []
        
    client = TavilyClient(api_key=api_key)
    
    all_results = []
    seen_urls = set()
    
    for query in queries:
        try:
            # We use basic search but request raw content.
            # Max 3 results per query to avoid overwhelming the LLM and respect the "top 5" rule.
            response = client.search(query, max_results=3, include_raw_content=True)
            
            for result in response.get("results", []):
                url = result.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append({
                        "title": result.get("title", ""),
                        "url": url,
                        "content": result.get("raw_content") or result.get("content", "")
                    })
                    
                    if len(all_results) >= 5:
                        return all_results
        except Exception as e:
            print(f"Error executing Tavily search for query '{query}': {e}")
            
    return all_results[:5]
