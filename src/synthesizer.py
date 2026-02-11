"""
Report Synthesizer — produces structured research reports with citations.
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from google import genai

from src.config import GOOGLE_API_KEY, MODEL_NAME, MAX_OUTPUT_TOKENS, TEMPERATURE

logger = logging.getLogger(__name__)

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client

SYNTHESIS_PROMPT = """You are an expert research analyst. Synthesize the following sources into a comprehensive, well-structured research report.

**Research Question:** {query}

**Sources:**
{sources_text}

**Instructions:**
1. Write a comprehensive report answering the research question
2. Use inline citations like [1], [2] etc. referencing the source numbers above
3. Structure with clear sections using markdown headers (##)
4. Start with an "Executive Summary" (2-3 sentences)
5. Include a "Key Findings" section with bullet points
6. Add a "Detailed Analysis" section with in-depth coverage
7. If sources contradict each other, note this explicitly in a "Conflicting Information" section
8. End with "Limitations & Gaps" noting what wasn't covered
9. Be factual and cite specific claims — never make up information
10. Write in a professional but accessible tone

**Report:**"""

COMPLETENESS_PROMPT = """You are a research quality evaluator. Given a research question and the findings so far, evaluate whether the research is comprehensive enough.

**Research Question:** {query}

**Current Findings:**
{findings}

**Evaluate:**
1. Is the answer comprehensive? (covers all major aspects)
2. Are there critical gaps? (important areas not addressed)
3. Are claims well-supported by sources?

**Respond with ONLY a JSON object:**
{{
  "is_complete": true/false,
  "completeness_score": 0.0-1.0,
  "gaps": ["gap1", "gap2"],
  "reasoning": "brief explanation"
}}"""


@dataclass
class ResearchReport:
    """A completed research report."""
    query: str
    report_markdown: str
    sources: List[Dict]
    iterations: int
    completeness_score: float = 0.0
    contradictions: List[Dict] = field(default_factory=list)


class ReportSynthesizer:
    """Synthesizes research findings into structured reports."""

    async def synthesize(
        self,
        query: str,
        sources: List[Dict],
        contradictions: Optional[List[Dict]] = None,
    ) -> str:
        """Generate a full research report from collected sources."""
        logger.info(f"Synthesizing report from {len(sources)} sources")

        # Format sources for the prompt
        sources_text = self._format_sources(sources)

        if contradictions:
            sources_text += "\n\n**Detected Contradictions:**\n"
            for c in contradictions:
                sources_text += f"- {c['source1']} vs {c['source2']}: {c['signal']}\n"

        prompt = SYNTHESIS_PROMPT.format(query=query, sources_text=sources_text)

        try:
            response = _get_client().models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={
                    "max_output_tokens": MAX_OUTPUT_TOKENS,
                    "temperature": TEMPERATURE,
                },
            )
            report = response.text.strip()

            # Append source references
            report += "\n\n---\n\n## Sources\n\n"
            for i, src in enumerate(sources, 1):
                credibility = src.get("credibility_score", 0)
                badge = "🟢" if credibility >= 0.8 else "🟡" if credibility >= 0.6 else "🔴"
                report += (
                    f"{i}. {badge} [{src.get('title', 'Untitled')}]({src.get('url', '#')}) "
                    f"— *{src.get('source_type', 'web')}* "
                    f"(credibility: {credibility:.0%})\n"
                )

            return report
        except Exception as e:
            logger.error(f"Report synthesis failed: {e}")
            return f"# Research Report\n\nFailed to synthesize report: {e}"

    async def evaluate_completeness(self, query: str, findings: str) -> Dict:
        """Evaluate if current findings are comprehensive enough."""
        logger.info("Evaluating research completeness")
        try:
            prompt = COMPLETENESS_PROMPT.format(query=query, findings=findings[:4000])
            response = _get_client().models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={"temperature": 0.1},
            )
            text = response.text.strip()
            # Parse JSON
            import json
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(text[start:end + 1])
        except Exception as e:
            logger.error(f"Completeness evaluation failed: {e}")

        return {"is_complete": True, "completeness_score": 0.7, "gaps": [], "reasoning": "Evaluation failed, proceeding with current findings."}

    def _format_sources(self, sources: List[Dict]) -> str:
        """Format sources for the synthesis prompt."""
        formatted = []
        for i, src in enumerate(sources, 1):
            content = src.get("content", "") or src.get("snippet", "")
            formatted.append(
                f"**[{i}] {src.get('title', 'Untitled')}**\n"
                f"Source: {src.get('url', 'N/A')} ({src.get('source_type', 'web')})\n"
                f"Credibility: {src.get('credibility_score', 0):.0%}\n"
                f"Content: {content}\n"
            )
        return "\n---\n".join(formatted)
