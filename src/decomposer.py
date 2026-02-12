"""
Query Decomposer — breaks complex questions into targeted sub-queries
and generates follow-up questions based on research gaps.
"""
import json
import logging
import time
from typing import List

from google import genai

from src.config import GOOGLE_API_KEY, MODEL_NAME, MAX_SUB_QUERIES

logger = logging.getLogger(__name__)

_client = None

def _get_client():
    """Get or create the Gemini API client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client

def _call_with_retry(func, max_retries=3, initial_delay=1.0):
    """
    Call a function with exponential backoff retry logic.
    
    Args:
        func: Function to call
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
    
    Returns:
        Result from the function call
    
    Raises:
        Exception: If all retries fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            error_msg = str(e).lower()
            
            # Check if it's a rate limit or transient error
            if "rate" in error_msg or "quota" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:
                    logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
            elif "500" in error_msg or "503" in error_msg or "timeout" in error_msg:
                if attempt < max_retries - 1:
                    logger.warning(f"Transient error, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    delay *= 1.5
                    continue
            
            # For other errors, fail immediately
            raise e
    
    raise last_exception

DECOMPOSE_PROMPT = """You are a research strategist. Given a complex research question, break it down into {max_queries} specific, searchable sub-queries that together will provide a comprehensive answer.

**Rules:**
- Each sub-query should target a different aspect of the question
- Make queries specific enough to return focused results
- Include queries for both foundational context AND cutting-edge developments
- Include at least one query targeting academic/scientific sources
- Return ONLY a JSON array of strings, no explanation

**Research Question:** {query}

**JSON array of sub-queries:**"""

FOLLOWUP_PROMPT = """You are a research analyst. Based on the findings so far, identify gaps in the research and generate {max_queries} follow-up questions to deepen the investigation.

**Original Question:** {query}

**Findings So Far:**
{findings}

**Rules:**
- Focus on areas where information is incomplete, contradictory, or superficial
- Target specific claims that need verification
- Explore implications and connections not yet covered
- Return ONLY a JSON array of strings, no explanation

**JSON array of follow-up queries:**"""


class QueryDecomposer:
    """Decomposes complex queries into searchable sub-queries."""

    async def decompose(self, query: str, max_queries: int = MAX_SUB_QUERIES) -> List[str]:
        """Break a complex question into targeted sub-queries with retry logic."""
        logger.info(f"Decomposing query: '{query}'")
        try:
            prompt = DECOMPOSE_PROMPT.format(query=query, max_queries=max_queries)
            
            def api_call():
                return _get_client().models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
                )
            
            response = _call_with_retry(api_call)
            text = response.text.strip()
            # Parse JSON array from response
            sub_queries = self._parse_json_array(text)
            logger.info(f"Generated {len(sub_queries)} sub-queries")
            return sub_queries[:max_queries]
        except Exception as e:
            logger.error(f"Query decomposition failed after retries: {e}")
            # Fallback: return the original query
            return [query]

    async def generate_followups(
        self, query: str, findings: str, max_queries: int = 3
    ) -> List[str]:
        """Generate follow-up questions based on current findings with retry logic."""
        logger.info("Generating follow-up questions")
        try:
            prompt = FOLLOWUP_PROMPT.format(
                query=query, findings=findings[:3000], max_queries=max_queries
            )
            
            def api_call():
                return _get_client().models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
                )
            
            response = _call_with_retry(api_call)
            text = response.text.strip()
            followups = self._parse_json_array(text)
            return followups[:max_queries]
        except Exception as e:
            logger.error(f"Follow-up generation failed after retries: {e}")
            return []

    @staticmethod
    def _parse_json_array(text: str) -> List[str]:
        """Extract a JSON array from LLM response text."""
        # Try direct parse
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return [str(item) for item in result]
        except json.JSONDecodeError:
            pass
        # Try to find JSON array in text
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1:
            try:
                result = json.loads(text[start:end + 1])
                if isinstance(result, list):
                    return [str(item) for item in result]
            except json.JSONDecodeError:
                pass
        # Fallback: split by newlines
        lines = [l.strip().strip('-•*').strip() for l in text.split('\n') if l.strip()]
        return [l for l in lines if len(l) > 10]
