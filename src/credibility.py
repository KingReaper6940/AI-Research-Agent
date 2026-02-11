"""
Credibility scoring — evaluates source reliability and detects contradictions.
"""
import logging
from typing import List, Dict
from urllib.parse import urlparse

from src.config import DOMAIN_SCORES, CREDIBILITY_THRESHOLD
from src.search import SearchResult

logger = logging.getLogger(__name__)


class CredibilityScorer:
    """Scores source credibility based on domain reputation, source type, and content signals."""

    # Source type base scores
    SOURCE_TYPE_SCORES = {
        "academic": 0.90,
        "wikipedia": 0.80,
        "web": 0.50,
    }

    def score(self, result: SearchResult) -> float:
        """Calculate credibility score (0.0 - 1.0) for a search result."""
        scores = []

        # 1. Domain reputation (highest weight)
        domain_score = self._domain_score(result.domain)
        scores.append(("domain", domain_score, 0.5))

        # 2. Source type
        type_score = self.SOURCE_TYPE_SCORES.get(result.source_type, 0.5)
        scores.append(("type", type_score, 0.25))

        # 3. Content quality signals
        content_score = self._content_quality(result)
        scores.append(("content", content_score, 0.25))

        # Weighted average
        total = sum(s * w for _, s, w in scores)
        result.credibility_score = round(total, 3)
        return result.credibility_score

    def score_all(self, results: List[SearchResult]) -> List[SearchResult]:
        """Score and filter all results by credibility threshold."""
        for r in results:
            self.score(r)
        # Sort by credibility (highest first)
        results.sort(key=lambda r: r.credibility_score, reverse=True)
        # Filter by threshold
        filtered = [r for r in results if r.credibility_score >= CREDIBILITY_THRESHOLD]
        removed = len(results) - len(filtered)
        if removed > 0:
            logger.info(f"Filtered {removed} low-credibility sources (threshold: {CREDIBILITY_THRESHOLD})")
        return filtered

    def _domain_score(self, domain: str) -> float:
        """Look up domain credibility score."""
        if not domain:
            return 0.4
        # Direct lookup
        if domain in DOMAIN_SCORES:
            return DOMAIN_SCORES[domain]
        # Check if it's a subdomain of a known domain
        parts = domain.split('.')
        for i in range(len(parts) - 1):
            parent = '.'.join(parts[i:])
            if parent in DOMAIN_SCORES:
                return DOMAIN_SCORES[parent]
        # Educational / government domains
        if domain.endswith('.edu') or domain.endswith('.ac.uk'):
            return 0.85
        if domain.endswith('.gov'):
            return 0.88
        if domain.endswith('.org'):
            return 0.65
        return 0.50

    def _content_quality(self, result: SearchResult) -> float:
        """Evaluate content quality based on signals."""
        score = 0.5
        content = result.content or result.snippet
        if not content:
            return 0.3

        # Longer, substantial content is generally better
        if len(content) > 1000:
            score += 0.15
        elif len(content) > 500:
            score += 0.10

        # Presence of data markers suggests factual content
        data_markers = ['%', 'study', 'research', 'data', 'according to', 'published',
                        'found that', 'results', 'evidence', 'analysis']
        marker_count = sum(1 for m in data_markers if m.lower() in content.lower())
        score += min(marker_count * 0.03, 0.15)

        # Academic indicators
        if result.source_type == "academic":
            score += 0.15

        return min(score, 1.0)

    @staticmethod
    def detect_contradictions(sources: List[Dict]) -> List[Dict]:
        """Identify potential contradictions between sources (basic heuristic)."""
        contradictions = []
        negation_pairs = [
            ("increase", "decrease"), ("rise", "fall"), ("higher", "lower"),
            ("growth", "decline"), ("benefit", "harm"), ("support", "oppose"),
            ("effective", "ineffective"), ("safe", "dangerous"),
            ("proven", "unproven"), ("confirm", "deny"),
        ]

        for i, s1 in enumerate(sources):
            for s2 in sources[i + 1:]:
                content1 = (s1.get("content", "") + s1.get("snippet", "")).lower()
                content2 = (s2.get("content", "") + s2.get("snippet", "")).lower()
                for pos, neg in negation_pairs:
                    if pos in content1 and neg in content2:
                        contradictions.append({
                            "source1": s1.get("title", ""),
                            "source2": s2.get("title", ""),
                            "signal": f"'{pos}' vs '{neg}'",
                        })
                    elif neg in content1 and pos in content2:
                        contradictions.append({
                            "source1": s1.get("title", ""),
                            "source2": s2.get("title", ""),
                            "signal": f"'{neg}' vs '{pos}'",
                        })
        return contradictions
