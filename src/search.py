"""
Search module — Web search via DuckDuckGo and Wikipedia retrieval.
"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import markdownify

from src.config import MAX_WEB_RESULTS, MAX_WIKIPEDIA_RESULTS, MAX_CONTENT_LENGTH, SEARCH_TIMEOUT

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result with metadata."""
    title: str
    url: str
    snippet: str
    content: str = ""
    source_type: str = "web"  # web, wikipedia, academic
    domain: str = ""
    credibility_score: float = 0.0

    def __post_init__(self):
        if not self.domain and self.url:
            try:
                self.domain = urlparse(self.url).netloc.replace("www.", "")
            except Exception:
                self.domain = ""


class WebSearcher:
    """Searches the web using DuckDuckGo."""

    def __init__(self):
        self.ddgs = DDGS()

    async def search(self, query: str, max_results: int = MAX_WEB_RESULTS) -> List[SearchResult]:
        """Search DuckDuckGo and return results with fetched content."""
        logger.info(f"Web search: '{query}'")
        try:
            raw_results = await asyncio.to_thread(
                self.ddgs.text, query, max_results=max_results
            )
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

        results = []
        for r in raw_results:
            result = SearchResult(
                title=r.get("title", ""),
                url=r.get("href", ""),
                snippet=r.get("body", ""),
                source_type="web",
            )
            results.append(result)

        # Fetch full content for top results (in parallel)
        await self._fetch_contents(results[:5])
        return results

    async def _fetch_contents(self, results: List[SearchResult]):
        """Fetch full page content for a list of results."""
        tasks = [self._fetch_content(r) for r in results]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _fetch_content(self, result: SearchResult):
        """Fetch and extract text content from a URL."""
        try:
            response = await asyncio.to_thread(
                lambda: requests.get(
                    result.url,
                    timeout=SEARCH_TIMEOUT,
                    headers={"User-Agent": "DeepResearchAgent/1.0 (research-bot)"},
                )
            )
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                # Remove noise elements
                for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
                    tag.decompose()
                # Extract main content
                main = soup.find("main") or soup.find("article") or soup.find("body")
                if main:
                    text = markdownify.markdownify(str(main), strip=["img", "a"])
                    result.content = text[:MAX_CONTENT_LENGTH].strip()
        except Exception as e:
            logger.debug(f"Failed to fetch {result.url}: {e}")


class WikipediaSearcher:
    """Retrieves Wikipedia articles for foundational context."""

    API_URL = "https://en.wikipedia.org/w/api.php"

    async def search(self, query: str, max_results: int = MAX_WIKIPEDIA_RESULTS) -> List[SearchResult]:
        """Search Wikipedia and return article summaries."""
        logger.info(f"Wikipedia search: '{query}'")
        try:
            # Step 1: Search for page titles
            search_params = {
                "action": "query", "list": "search", "srsearch": query,
                "srlimit": max_results, "format": "json",
            }
            resp = await asyncio.to_thread(
                lambda: requests.get(self.API_URL, params=search_params, timeout=SEARCH_TIMEOUT)
            )
            data = resp.json()
            pages = data.get("query", {}).get("search", [])

            results = []
            for page in pages:
                title = page["title"]
                # Step 2: Get extract for each page
                extract_params = {
                    "action": "query", "titles": title, "prop": "extracts",
                    "exintro": True, "explaintext": True, "format": "json",
                }
                ext_resp = await asyncio.to_thread(
                    lambda t=title, p=extract_params: requests.get(
                        self.API_URL, params=p, timeout=SEARCH_TIMEOUT
                    )
                )
                ext_data = ext_resp.json()
                page_data = list(ext_data.get("query", {}).get("pages", {}).values())
                content = page_data[0].get("extract", "") if page_data else ""

                results.append(SearchResult(
                    title=title,
                    url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    snippet=content[:300],
                    content=content[:MAX_CONTENT_LENGTH],
                    source_type="wikipedia",
                    domain="en.wikipedia.org",
                ))
            return results
        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
            return []
