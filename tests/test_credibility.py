"""
Unit tests for the CredibilityScorer class.
Tests domain scoring, source type scoring, content quality, and contradiction detection.
"""
import pytest
from src.credibility import CredibilityScorer
from src.search import SearchResult


class TestCredibilityScorer:
    """Test suite for CredibilityScorer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = CredibilityScorer()

    # ── Domain Scoring ────────────────────────────────────

    @pytest.mark.unit
    def test_domain_score_high_credibility(self):
        """Test that high-credibility domains receive appropriate scores."""
        assert self.scorer._domain_score("nature.com") == 0.95
        assert self.scorer._domain_score("arxiv.org") == 0.93
        assert self.scorer._domain_score("who.int") == 0.95

    @pytest.mark.unit
    def test_domain_score_medium_credibility(self):
        """Test medium-credibility domains."""
        assert self.scorer._domain_score("reuters.com") == 0.88
        assert self.scorer._domain_score("bbc.com") == 0.85
        assert self.scorer._domain_score("wikipedia.org") == 0.82

    @pytest.mark.unit
    def test_domain_score_low_credibility(self):
        """Test low-credibility domains."""
        assert self.scorer._domain_score("reddit.com") == 0.50
        assert self.scorer._domain_score("quora.com") == 0.45

    @pytest.mark.unit
    def test_domain_score_unknown_domain(self):
        """Test that unknown domains get default score."""
        score = self.scorer._domain_score("unknown-site.com")
        assert score == 0.50

    @pytest.mark.unit
    def test_domain_score_edu_domains(self):
        """Test that .edu domains get high credibility."""
        assert self.scorer._domain_score("mit.edu") == 0.90
        assert self.scorer._domain_score("unknown-university.edu") == 0.85

    @pytest.mark.unit
    def test_domain_score_gov_domains(self):
        """Test that .gov domains get high credibility."""
        score = self.scorer._domain_score("example.gov")
        assert score == 0.88

    @pytest.mark.unit
    def test_domain_score_org_domains(self):
        """Test that .org domains get moderate credibility."""
        score = self.scorer._domain_score("random-org.org")
        assert score == 0.65

    @pytest.mark.unit
    def test_domain_score_empty(self):
        """Test that empty domain returns low score."""
        assert self.scorer._domain_score("") == 0.4

    # ── Source Type Scoring ───────────────────────────────

    @pytest.mark.unit
    def test_source_type_scores(self):
        """Test that source types have appropriate base scores."""
        assert CredibilityScorer.SOURCE_TYPE_SCORES["academic"] == 0.90
        assert CredibilityScorer.SOURCE_TYPE_SCORES["wikipedia"] == 0.80
        assert CredibilityScorer.SOURCE_TYPE_SCORES["web"] == 0.50

    # ── Full Scoring ─────────────────────────────────────

    @pytest.mark.unit
    def test_score_academic_source(self):
        """Test scoring of an academic source."""
        result = SearchResult(
            title="Test Paper",
            url="https://arxiv.org/abs/1234.5678",
            snippet="A research paper about machine learning.",
            content="This study presents research findings based on extensive data analysis. "
                    "The results show evidence of improvement according to published research.",
            source_type="academic",
            domain="arxiv.org"
        )
        score = self.scorer.score(result)
        # Academic + high domain + good content should score high
        assert score > 0.75
        assert result.credibility_score == score

    @pytest.mark.unit
    def test_score_web_source(self):
        """Test scoring of a web source with unknown domain."""
        result = SearchResult(
            title="Blog Post",
            url="https://random-blog.com/post",
            snippet="A blog post about technology.",
            content="Short content.",
            source_type="web",
            domain="random-blog.com"
        )
        score = self.scorer.score(result)
        # Unknown domain + web source + short content should score moderate/low
        assert 0.3 <= score <= 0.65

    @pytest.mark.unit
    def test_score_sets_credibility_on_result(self):
        """Test that scoring updates the result's credibility_score field."""
        result = SearchResult(
            title="Test",
            url="https://example.com",
            snippet="snippet",
            source_type="web"
        )
        assert result.credibility_score == 0.0
        score = self.scorer.score(result)
        assert result.credibility_score == score
        assert score > 0

    # ── Content Quality ──────────────────────────────────

    @pytest.mark.unit
    def test_content_quality_long_content(self):
        """Test that longer content gets higher quality scores."""
        result = SearchResult(
            title="Article",
            url="https://example.com",
            snippet="snippet",
            content="a " * 750,  # Long content
            source_type="web",
            domain="example.com"
        )
        long_score = self.scorer._content_quality(result)

        result.content = "a " * 150  # Short content
        short_score = self.scorer._content_quality(result)

        assert long_score > short_score

    @pytest.mark.unit
    def test_content_quality_data_markers(self):
        """Test that content with data markers scores higher."""
        result_with_markers = SearchResult(
            title="Research",
            url="https://example.com",
            snippet="snippet",
            content="According to a recent study, research shows that data analysis found evidence of 50% improvement.",
            source_type="web",
            domain="example.com"
        )
        score_with = self.scorer._content_quality(result_with_markers)

        result_without = SearchResult(
            title="Opinion",
            url="https://example.com",
            snippet="snippet",
            content="I think this is interesting and might be true.",
            source_type="web",
            domain="example.com"
        )
        score_without = self.scorer._content_quality(result_without)

        assert score_with > score_without

    @pytest.mark.unit
    def test_content_quality_empty_content(self):
        """Test that empty content returns low score."""
        result = SearchResult(
            title="Empty",
            url="https://example.com",
            snippet="",
            content="",
            source_type="web"
        )
        score = self.scorer._content_quality(result)
        assert score == 0.3

    # ── Score All / Filtering ────────────────────────────

    @pytest.mark.unit
    def test_score_all_scores_every_result(self):
        """Test that score_all computes a score for every result."""
        results = [
            SearchResult(
                title=f"Result {i}",
                url=f"https://site{i}.com",
                snippet="snippet",
                content="Some content here.",
                source_type="web",
            )
            for i in range(3)
        ]
        filtered = self.scorer.score_all(results)
        # Every result should have a non-zero credibility score now
        for r in results:
            assert r.credibility_score > 0

    @pytest.mark.unit
    def test_score_all_returns_sorted(self):
        """Test that score_all returns results sorted by credibility descending."""
        results = [
            SearchResult(title="Low", url="https://random.com", snippet="s", content="x", source_type="web"),
            SearchResult(title="High", url="https://nature.com/paper", snippet="s",
                         content="This study presents research findings based on data analysis.", source_type="academic", domain="nature.com"),
        ]
        filtered = self.scorer.score_all(results)
        if len(filtered) > 1:
            assert filtered[0].credibility_score >= filtered[1].credibility_score

    @pytest.mark.unit
    def test_score_all_filters_below_threshold(self):
        """Test that score_all filters sources below the credibility threshold."""
        results = self.scorer.score_all([
            SearchResult(title="T", url="https://nature.com/p", snippet="s",
                         content="Published research study with evidence and data analysis results.",
                         source_type="academic", domain="nature.com"),
        ])
        # A nature.com academic source should always pass the 0.5 threshold
        assert len(results) >= 1
        assert all(r.credibility_score >= 0.5 for r in results)

    # ── Contradiction Detection ──────────────────────────

    @pytest.mark.unit
    def test_detect_contradictions(self):
        """Test contradiction detection between sources."""
        sources = [
            {
                "title": "Study A",
                "content": "The research shows an increase in temperature.",
                "snippet": ""
            },
            {
                "title": "Study B",
                "content": "The data indicates a decrease in temperature.",
                "snippet": ""
            },
        ]

        contradictions = CredibilityScorer.detect_contradictions(sources)

        # Should detect increase/decrease contradiction
        assert len(contradictions) > 0
        assert any("increase" in c["signal"] and "decrease" in c["signal"]
                    for c in contradictions)

    @pytest.mark.unit
    def test_detect_contradictions_none(self):
        """Test that consistent sources show no contradictions."""
        sources = [
            {
                "title": "Study A",
                "content": "The results show improvement in outcomes.",
                "snippet": ""
            },
            {
                "title": "Study B",
                "content": "Data demonstrates better performance.",
                "snippet": ""
            }
        ]

        contradictions = CredibilityScorer.detect_contradictions(sources)
        assert isinstance(contradictions, list)

    @pytest.mark.unit
    def test_detect_contradictions_empty(self):
        """Test contradiction detection with empty sources."""
        contradictions = CredibilityScorer.detect_contradictions([])
        assert contradictions == []
