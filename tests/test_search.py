"""
Unit tests for search functionality.
Tests SearchResult dataclass and basic search module functionality.
"""
import pytest
from src.search import SearchResult


class TestSearchResult:
    """Test suite for SearchResult dataclass."""

    @pytest.mark.unit
    def test_search_result_initialization(self):
        """Test basic SearchResult creation."""
        result = SearchResult(
            title="Test Article",
            url="https://example.com/article",
            snippet="This is a test snippet",
            content="Full content here",
            source_type="web"
        )
        
        assert result.title == "Test Article"
        assert result.url == "https://example.com/article"
        assert result.snippet == "This is a test snippet"
        assert result.content == "Full content here"
        assert result.source_type == "web"
        assert result.credibility_score == 0.0  # Default value

    @pytest.mark.unit
    def test_search_result_domain_extraction(self):
        """Test that domain is automatically extracted from URL."""
        result = SearchResult(
            title="Test",
            url="https://www.example.com/path/to/page",
            snippet="snippet",
            source_type="web"
        )
        
        assert result.domain == "example.com"

    @pytest.mark.unit
    def test_search_result_domain_extraction_no_www(self):
        """Test domain extraction without www prefix."""
        result = SearchResult(
            title="Test",
            url="https://subdomain.example.org/page",
            snippet="snippet",
            source_type="web"
        )
        
        assert result.domain == "subdomain.example.org"

    @pytest.mark.unit
    def test_search_result_domain_extraction_with_www(self):
        """Test that www. is removed from domain."""
        result = SearchResult(
            title="Test",
            url="https://www.bbc.com/news",
            snippet="snippet",
            source_type="web"
        )
        
        assert result.domain == "bbc.com"

    @pytest.mark.unit
    def test_search_result_invalid_url(self):
        """Test handling of invalid URL."""
        result = SearchResult(
            title="Test",
            url="not-a-valid-url",
            snippet="snippet",
            source_type="web"
        )
        
        # Should handle gracefully
        assert result.domain == ""

    @pytest.mark.unit
    def test_search_result_empty_url(self):
        """Test handling of empty URL."""
        result = SearchResult(
            title="Test",
            url="",
            snippet="snippet",
            source_type="web"
        )
        
        assert result.domain == ""

    @pytest.mark.unit
    def test_search_result_default_values(self):
        """Test default values for optional fields."""
        result = SearchResult(
            title="Test",
            url="https://example.com",
            snippet="snippet"
        )
        
        assert result.content == ""
        assert result.source_type == "web"
        assert result.domain == "example.com"
        assert result.credibility_score == 0.0

    @pytest.mark.unit
    def test_search_result_source_types(self):
        """Test different source type values."""
        for source_type in ["web", "wikipedia", "academic"]:
            result = SearchResult(
                title="Test",
                url="https://example.com",
                snippet="snippet",
                source_type=source_type
            )
            assert result.source_type == source_type

    @pytest.mark.unit
    def test_search_result_credibility_assignment(self):
        """Test that credibility score can be assigned."""
        result = SearchResult(
            title="Test",
            url="https://example.com",
            snippet="snippet",
            credibility_score=0.85
        )
        
        assert result.credibility_score == 0.85

    @pytest.mark.unit
    def test_search_result_domain_special_cases(self):
        """Test domain extraction for special cases."""
        # ArXiv URL
        result = SearchResult(
            title="Paper",
            url="https://arxiv.org/abs/2101.12345",
            snippet="snippet",
            source_type="academic"
        )
        assert result.domain == "arxiv.org"
        
        # Wikipedia URL
        result = SearchResult(
            title="Article",
            url="https://en.wikipedia.org/wiki/Python",
            snippet="snippet",
            source_type="wikipedia"
        )
        assert result.domain == "en.wikipedia.org"


# Note: Integration tests for actual web search, Wikipedia, and academic search
# would require mocking or network access. These should be in separate test files
# marked as integration tests and potentially slow tests.
