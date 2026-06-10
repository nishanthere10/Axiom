import os
import logging
import concurrent.futures
from tavily import TavilyClient
from core.config import settings
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

def search_tavily(queries: list[str]) -> list[dict]:
    """
    Executes search queries using Tavily concurrently and returns a list of unique results.
    Each result contains 'title', 'url', and 'raw_content' (if available).
    """
    api_key = settings.TAVILY_API_KEY
    if not api_key:
        logger.warning("TAVILY_API_KEY not set. Returning empty results.")
        return []
        
    client = TavilyClient(api_key=api_key)
    
    @retry(stop=stop_after_attempt(2), wait=wait_fixed(2))
    def fetch_query(q):
        try:
            return client.search(q, max_results=3, include_raw_content=True)
        except Exception as e:
            logger.error("Error executing Tavily search for query '%s': %s", q, e)
            raise e

    all_results = []
    seen_urls = set()

    # Limit to top 3 queries to avoid rate limits and save time
    top_queries = queries[:3]

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(fetch_query, q) for q in top_queries]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                response = future.result()
            except Exception as e:
                logger.error("Tavily search failed after retries: %s", e)
                continue
                
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
                        
    return all_results[:5]
