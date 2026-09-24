"""Web search action."""

import re
from typing import Any
import httpx

from app.actions.base import BaseAction


class SearchAction(BaseAction):
    """Search the web for information."""

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Search the web for information"

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the action with given parameters."""
        query = params.get("query")
        if not query:
            return {"success": False, "message": "Missing 'query' parameter."}
            
        try:
            url = f"https://html.duckduckgo.com/html/?q={query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
            html = response.text
            results = []
            
            # Simple string parsing for class="result__title" and class="result__snippet"
            parts = html.split('class="result ')
            for part in parts[1:6]:  # top 5 results
                title = "No Title"
                url_str = ""
                snippet = "No Snippet"
                
                title_start = part.find('class="result__title"')
                if title_start != -1:
                    a_start = part.find('<a class="result__url"', title_start)
                    if a_start != -1:
                        href_start = part.find('href="', a_start) + 6
                        href_end = part.find('"', href_start)
                        url_str = part[href_start:href_end]
                        text_start = part.find('>', a_start) + 1
                        text_end = part.find('</a>', text_start)
                        title_html = part[text_start:text_end]
                        title = re.sub(r'<[^>]+>', '', title_html).strip()
                
                snippet_start = part.find('class="result__snippet"')
                if snippet_start != -1:
                    text_start = part.find('>', snippet_start) + 1
                    text_end = part.find('</a>', text_start)
                    snippet_html = part[text_start:text_end]
                    snippet = re.sub(r'<[^>]+>', '', snippet_html).strip()
                
                if url_str:
                    if url_str.startswith('//'):
                        url_str = "https:" + url_str
                    results.append({
                        "title": title,
                        "snippet": snippet,
                        "url": url_str
                    })
                    
            return {
                "success": True,
                "message": f"Found {len(results)} results.",
                "results": results
            }
            
        except Exception as e:
            return {"success": False, "message": f"Search failed: {e}"}
