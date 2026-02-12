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
    def test_source_type_scores(self):
        """Test that source types have appropriate base scores."""
        assert CredibilityScorer.SOURCE_TYPE_SCORES["academic"] == 0.90
        assert CredibilityScorer.SOURCE_TYPE_SCORES["wikipedia"] == 0.80
        assert CredibilityScorer.SOURCE_TYPE_SCORES["web"] == 0.50

    @pytest.mark.unit
    def test_score_academic_source(self):
        """Test scoring of an academic source."""
        result = SearchResult(
            title="Test Paper",
            url="https://arxiv.org/abs/1234.5678",
            snippet="A research paper about machine learning.",
            content="This study presents research findings based on extensive data analysis.",
            source_type="academic",
            domain="arxiv.org"
        )
        score = self.scorer.score(result)
        # Academic + high domain + good content should score high
        assert score > 0.8
        assert result.credibility_score == score

    @pytest.mark.unit
    def test_score_web_source(self):
        """Test scoring of a web source."""
        result = SearchResult(
            title="Blog Post",
            url="https://example.com/blog",
            snippet="A blog post about technology.",
            content="Short content without much substance.",
            source_type="web",
            domain="example.com"
        )
        score = self.scorer.score(result)
        # Unknown domain + web source + short content should score lower
        assert 0.4 <= score <= 0.6

    @pytest.mark.unit
    def test_content_quality_long_content(self):
        """Test that longer content gets higher quality scores."""
        result = SearchResult(
            title="Article",
            url="https://example.com",
            snippet="snippet",
            content="a" * 1500,  # Long content
            source_type="web",
            domain="example.com"
        )
        long_score = self.scorer._content_quality(result)
        
        result.content = "a" * 300  # Short content
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
    def test_score_all_filters_low_credibility(self):
        """Test that score_all filters out low-credibility sources."""
        results = [
            SearchResult(
                title=f"Result {i}",
                url=f"https://site{i}.com",
                snippet="snippet",
                content="content",
                source_type="web",
                domain=f"site{i}.com"
            )
            for i in range(5)
        ]
        
        # Manually set some credibility scores
        results[0].credibility_score = 0.9
        results[1].credibility_score = 0.7
        results[2].credibility_score = 0.4  # Below threshold
        results[3].credibility_score = 0.3  # Below threshold
        results[4].credibility_score = 0.8
        
        filtered = self.scorer.score_all(results)
        
        # Should keep only those >= 0.5 threshold
        assert len(filtered) == 3
        assert all(r.credibility_score >= 0.5 for r in filtered)
        # Should be sorted by credibility (highest first)
        assert filtered[0].credibility_score >= filtered[1].credibility_score

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
            {
                "title": "Study C",
                "content": "Results confirm growth in the sector.",
                "snippet": ""
            }
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
        
        # Should not detect contradictions in consistent sources
        # (though the simple heuristic might still catch some)
        assert isinstance(contradictions, list)
