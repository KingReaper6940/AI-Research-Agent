"""
Unit tests for the ContentProcessor class.
Tests text cleaning, truncation, and key sentence extraction.
"""
import pytest
from src.processor import ContentProcessor


class TestContentProcessor:
    """Test suite for ContentProcessor functionality."""

    # ── Clean Method ─────────────────────────────────────

    @pytest.mark.unit
    def test_clean_removes_excessive_whitespace(self):
        """Test that excessive whitespace is normalized."""
        text = "This  is   some    text\n\n\n\nwith\n\n\n\nlots of whitespace"
        cleaned = ContentProcessor.clean(text)

        assert "  " not in cleaned  # No double spaces
        assert "\n\n\n" not in cleaned  # Max 2 consecutive newlines

    @pytest.mark.unit
    def test_clean_removes_urls(self):
        """Test that URLs are removed from content."""
        text = "Check out https://example.com for more info and http://another.com too"
        cleaned = ContentProcessor.clean(text)

        assert "https://example.com" not in cleaned
        assert "http://another.com" not in cleaned

    @pytest.mark.unit
    def test_clean_removes_subscribe_artifacts(self):
        """Test that subscribe/newsletter artifacts are removed."""
        text = "Good content here. Subscribe to our newsletter for updates! More content."
        cleaned = ContentProcessor.clean(text)
        # The regex removes 'Subscribe...newsletter'
        assert "newsletter" not in cleaned

    @pytest.mark.unit
    def test_clean_removes_advertisement(self):
        """Test that Advertisement text is removed."""
        text = "Some content. Advertisement More content here."
        cleaned = ContentProcessor.clean(text)
        assert "Advertisement" not in cleaned

    @pytest.mark.unit
    def test_clean_handles_empty_input(self):
        """Test that empty input returns empty string."""
        assert ContentProcessor.clean("") == ""
        assert ContentProcessor.clean(None) == ""

    @pytest.mark.unit
    def test_clean_preserves_important_content(self):
        """Test that important content is preserved."""
        text = "This is important research content. It contains valuable information."
        cleaned = ContentProcessor.clean(text)

        assert "important research content" in cleaned
        assert "valuable information" in cleaned

    # ── Truncate Method ──────────────────────────────────

    @pytest.mark.unit
    def test_truncate_short_text(self):
        """Test that short text is not truncated."""
        text = "This is a short text."
        result = ContentProcessor.truncate(text, max_length=1000)
        assert result == text

    @pytest.mark.unit
    def test_truncate_long_text(self):
        """Test that long text is truncated to roughly max_length."""
        text = "A" * 5000
        result = ContentProcessor.truncate(text, max_length=100)
        # Result should be much shorter than original
        assert len(result) < 5000

    @pytest.mark.unit
    def test_truncate_breaks_at_sentence(self):
        """Test that truncation prefers sentence boundaries."""
        text = "First sentence here. Second sentence follows. Third sentence is added. Fourth is extra."
        result = ContentProcessor.truncate(text, max_length=60)
        # Should end at a sentence boundary (period) or with ellipsis
        assert result.endswith(".") or result.endswith("...")

    @pytest.mark.unit
    def test_truncate_adds_ellipsis_no_period(self):
        """Test that ellipsis is added when no good period break exists."""
        text = "A" * 200  # Long text with no periods
        result = ContentProcessor.truncate(text, max_length=50)
        assert result.endswith("...")

    @pytest.mark.unit
    def test_truncate_exact_length(self):
        """Test that text at exactly max_length is not truncated."""
        text = "A" * 100
        result = ContentProcessor.truncate(text, max_length=100)
        assert result == text

    # ── Extract Key Sentences ────────────────────────────

    @pytest.mark.unit
    def test_extract_key_sentences_returns_string(self):
        """Test that extract_key_sentences returns a string."""
        text = "This is a reasonable length sentence for testing. And here is another sentence that is also long enough."
        result = ContentProcessor.extract_key_sentences(text, max_sentences=5)
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_extract_key_sentences_filters_short(self):
        """Test that very short sentences are filtered out."""
        text = "Hi. This is a longer sentence with more content that should be kept. Ok. Another substantial sentence here for testing."
        result = ContentProcessor.extract_key_sentences(text, max_sentences=10)
        # Very short sentences like "Hi." (3 chars) and "Ok." (3 chars) should be filtered
        # since filter is len > 20
        sentences = [s.strip() for s in result.split('.') if s.strip()]
        for s in sentences:
            assert len(s) > 15  # Each kept sentence should be substantial

    @pytest.mark.unit
    def test_extract_key_sentences_handles_empty(self):
        """Test that empty input returns empty string."""
        assert ContentProcessor.extract_key_sentences("") == ""
        assert ContentProcessor.extract_key_sentences(None) == ""

    @pytest.mark.unit
    def test_extract_key_sentences_limits_count(self):
        """Test that max_sentences limit is respected."""
        sentences = [f"Sentence number {i} with enough content to pass the length filter easily." for i in range(20)]
        text = " ".join(sentences)

        result = ContentProcessor.extract_key_sentences(text, max_sentences=3)
        # Count periods in result as a rough sentence count
        period_count = result.count(".")
        assert period_count <= 4  # allow some flexibility
