"""
Research Agent — the autonomous iterative research loop.
Orchestrates: decompose → search → process → evaluate → repeat or synthesize.
"""
import asyncio
import logging
import time
from typing import List, Dict, Callable, Optional, Any
from dataclasses import dataclass, field, asdict

from src.search import WebSearcher, WikipediaSearcher, SearchResult
from src.academic import ArxivSearcher, SemanticScholarSearcher
from src.decomposer import QueryDecomposer
from src.credibility import CredibilityScorer
from src.synthesizer import ReportSynthesizer, ResearchReport
from src.processor import ContentProcessor
from src.config import MAX_RESEARCH_ITERATIONS

logger = logging.getLogger(__name__)


@dataclass
class ResearchEvent:
    """An event emitted during research for real-time progress tracking."""
    event_type: str       # "status", "sub_query", "source_found", "iteration", "synthesis", "complete", "error"
    message: str
    data: Optional[Dict] = None
    timestamp: float = field(default_factory=time.time)


class ResearchAgent:
    """
    Autonomous research agent that iteratively gathers and synthesizes information.

    Flow:
    1. Decompose the query into sub-queries
    2. Search web, Wikipedia, and academic sources for each sub-query
    3. Score source credibility and filter
    4. Evaluate if more research is needed
    5. If yes → generate follow-up queries → repeat from step 2
    6. If no → synthesize final report with citations
    """

    def __init__(self):
        self.web_searcher = WebSearcher()
        self.wiki_searcher = WikipediaSearcher()
        self.arxiv_searcher = ArxivSearcher()
        self.scholar_searcher = SemanticScholarSearcher()
        self.decomposer = QueryDecomposer()
        self.credibility_scorer = CredibilityScorer()
        self.synthesizer = ReportSynthesizer()
        self.processor = ContentProcessor()

    async def research(
        self,
        query: str,
        on_event: Optional[Callable[[ResearchEvent], Any]] = None,
    ) -> ResearchReport:
        """
        Execute the full autonomous research loop.

        Args:
            query: The research question
            on_event: Optional callback for real-time progress events
        """
        all_sources: List[Dict] = []
        all_contradictions: List[Dict] = []

        async def emit(event_type: str, message: str, data: Optional[Dict] = None):
            event = ResearchEvent(event_type=event_type, message=message, data=data)
            if on_event:
                result = on_event(event)
                if asyncio.iscoroutine(result):
                    await result
            logger.info(f"[{event_type}] {message}")

        await emit("status", f"Starting research: \"{query}\"")

        # ── Iteration Loop ────────────────────────────────────
        current_query = query
        for iteration in range(1, MAX_RESEARCH_ITERATIONS + 1):
            await emit("iteration", f"Research iteration {iteration}/{MAX_RESEARCH_ITERATIONS}", {
                "iteration": iteration,
                "max_iterations": MAX_RESEARCH_ITERATIONS,
            })

            # Step 1: Decompose query
            await emit("status", "Decomposing query into sub-queries...")
            sub_queries = await self.decomposer.decompose(current_query)

            for sq in sub_queries:
                await emit("sub_query", sq, {"query": sq})

            # Step 2: Search all sources in parallel
            await emit("status", f"Searching {len(sub_queries)} sub-queries across web, Wikipedia, and academic sources...")
            iteration_sources = await self._search_all(sub_queries, emit)

            # Step 3: Process and clean content
            for src in iteration_sources:
                src["content"] = self.processor.clean(src.get("content", ""))
                src["content"] = self.processor.truncate(src["content"])

            # Step 4: Score credibility
            await emit("status", "Scoring source credibility...")
            result_objects = [SearchResult(**{k: v for k, v in s.items() if k in SearchResult.__dataclass_fields__}) for s in iteration_sources]
            filtered = self.credibility_scorer.score_all(result_objects)
            iteration_sources = [
                {**asdict(r)} for r in filtered
            ]

            # Detect contradictions
            new_contradictions = self.credibility_scorer.detect_contradictions(iteration_sources)
            all_contradictions.extend(new_contradictions)
            if new_contradictions:
                await emit("status", f"⚠️ Detected {len(new_contradictions)} potential contradictions")

            # Add to cumulative sources (deduplicate by URL)
            existing_urls = {s["url"] for s in all_sources}
            for src in iteration_sources:
                if src["url"] not in existing_urls:
                    all_sources.append(src)
                    existing_urls.add(src["url"])
                    await emit("source_found", src.get("title", ""), {
                        "url": src.get("url", ""),
                        "source_type": src.get("source_type", "web"),
                        "credibility_score": src.get("credibility_score", 0),
                        "domain": src.get("domain", ""),
                    })

            await emit("status", f"Collected {len(all_sources)} total sources")

            # Step 5: Evaluate completeness (skip on last iteration)
            if iteration < MAX_RESEARCH_ITERATIONS:
                findings_summary = "\n".join(
                    f"- {s.get('title', '')}: {s.get('snippet', '')}" for s in all_sources[:20]
                )
                eval_result = await self.synthesizer.evaluate_completeness(query, findings_summary)
                completeness = eval_result.get("completeness_score", 0.7)

                await emit("status", f"Completeness: {completeness:.0%}", {"completeness_score": completeness})

                if eval_result.get("is_complete", False) and completeness >= 0.8:
                    await emit("status", f"Research is comprehensive enough ({completeness:.0%}). Moving to synthesis.")
                    break

                # Generate follow-up queries for next iteration
                gaps = eval_result.get("gaps", [])
                if gaps:
                    await emit("status", f"Identified {len(gaps)} gaps. Generating follow-up queries...")
                    followups = await self.decomposer.generate_followups(query, findings_summary)
                    current_query = query + " " + " ".join(followups)
                else:
                    break

        # ── Synthesis ─────────────────────────────────────────
        await emit("synthesis", f"Synthesizing report from {len(all_sources)} sources...")
        report_md = await self.synthesizer.synthesize(
            query=query,
            sources=all_sources,
            contradictions=all_contradictions if all_contradictions else None,
        )

        report = ResearchReport(
            query=query,
            report_markdown=report_md,
            sources=all_sources,
            iterations=iteration,
            contradictions=all_contradictions,
        )

        await emit("complete", "Research complete!", {
            "total_sources": len(all_sources),
            "iterations": iteration,
            "contradictions": len(all_contradictions),
        })

        return report

    async def _search_all(
        self, sub_queries: List[str], emit: Callable
    ) -> List[Dict]:
        """Search all source types for all sub-queries in parallel."""
        all_results: List[Dict] = []

        async def search_sub_query(sq: str):
            results = []
            # Run all search types in parallel
            web_task = self.web_searcher.search(sq)
            wiki_task = self.wiki_searcher.search(sq)
            arxiv_task = self.arxiv_searcher.search(sq)
            scholar_task = self.scholar_searcher.search(sq)

            web_results, wiki_results, arxiv_results, scholar_results = await asyncio.gather(
                web_task, wiki_task, arxiv_task, scholar_task,
                return_exceptions=True,
            )

            for source_results in [web_results, wiki_results, arxiv_results, scholar_results]:
                if isinstance(source_results, Exception):
                    logger.error(f"Search failed: {source_results}")
                    continue
                for r in source_results:
                    results.append(asdict(r))

            return results

        # Run all sub-queries in parallel
        tasks = [search_sub_query(sq) for sq in sub_queries]
        results_per_query = await asyncio.gather(*tasks, return_exceptions=True)

        for result_set in results_per_query:
            if isinstance(result_set, Exception):
                logger.error(f"Sub-query search failed: {result_set}")
                continue
            all_results.extend(result_set)

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in all_results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(r)

        return unique_results
