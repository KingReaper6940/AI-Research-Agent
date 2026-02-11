"""
Academic search module — ArXiv and Semantic Scholar integration.
"""
import asyncio
import logging
from typing import List

import arxiv
import requests

from src.config import MAX_ACADEMIC_RESULTS, SEARCH_TIMEOUT, MAX_CONTENT_LENGTH
from src.search import SearchResult

logger = logging.getLogger(__name__)


class ArxivSearcher:
    """Searches ArXiv for academic papers."""

    async def search(self, query: str, max_results: int = MAX_ACADEMIC_RESULTS) -> List[SearchResult]:
        """Search ArXiv and return paper metadata + abstracts."""
        logger.info(f"ArXiv search: '{query}'")
        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            raw_results = await asyncio.to_thread(lambda: list(client.results(search)))

            results = []
            for paper in raw_results:
                authors = ", ".join(a.name for a in paper.authors[:5])
                if len(paper.authors) > 5:
                    authors += f" et al. ({len(paper.authors)} authors)"

                content = (
                    f"**{paper.title}**\n\n"
                    f"**Authors**: {authors}\n"
                    f"**Published**: {paper.published.strftime('%Y-%m-%d')}\n"
                    f"**Categories**: {', '.join(paper.categories)}\n\n"
                    f"**Abstract**: {paper.summary}\n"
                )

                results.append(SearchResult(
                    title=paper.title,
                    url=paper.entry_id,
                    snippet=paper.summary[:300],
                    content=content[:MAX_CONTENT_LENGTH],
                    source_type="academic",
                    domain="arxiv.org",
                ))
            return results
        except Exception as e:
            logger.error(f"ArXiv search failed: {e}")
            return []


class SemanticScholarSearcher:
    """Searches Semantic Scholar for academic papers with citation data."""

    API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    async def search(self, query: str, max_results: int = MAX_ACADEMIC_RESULTS) -> List[SearchResult]:
        """Search Semantic Scholar and return papers with citation counts."""
        logger.info(f"Semantic Scholar search: '{query}'")
        try:
            params = {
                "query": query,
                "limit": max_results,
                "fields": "title,abstract,authors,year,citationCount,url,externalIds",
            }
            resp = await asyncio.to_thread(
                lambda: requests.get(self.API_URL, params=params, timeout=SEARCH_TIMEOUT)
            )
            if resp.status_code != 200:
                logger.error(f"Semantic Scholar API returned {resp.status_code}")
                return []

            data = resp.json()
            results = []
            for paper in data.get("data", []):
                if not paper.get("abstract"):
                    continue

                authors_list = paper.get("authors", [])
                authors = ", ".join(a.get("name", "") for a in authors_list[:5])
                if len(authors_list) > 5:
                    authors += f" et al."

                citation_count = paper.get("citationCount", 0)
                year = paper.get("year", "N/A")

                content = (
                    f"**{paper['title']}**\n\n"
                    f"**Authors**: {authors}\n"
                    f"**Year**: {year}\n"
                    f"**Citations**: {citation_count}\n\n"
                    f"**Abstract**: {paper['abstract']}\n"
                )

                paper_url = paper.get("url", "")
                if not paper_url:
                    ext_ids = paper.get("externalIds", {})
                    doi = ext_ids.get("DOI", "")
                    if doi:
                        paper_url = f"https://doi.org/{doi}"

                results.append(SearchResult(
                    title=paper["title"],
                    url=paper_url,
                    snippet=paper["abstract"][:300],
                    content=content[:MAX_CONTENT_LENGTH],
                    source_type="academic",
                    domain="semanticscholar.org",
                ))
            return results
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            return []
