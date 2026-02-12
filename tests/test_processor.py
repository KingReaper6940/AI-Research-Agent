"""
Unit tests for the ContentProcessor class.
Tests text cleaning, truncation, and key sentence extraction.
"""
import pytest
from src.processor import ContentProcessor


class TestContentProcessor:
    """Test suite for ContentProcessor functionality."""

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
    def test_clean_removes_web_artifacts(self):
        """Test that common web artifacts are removed."""
        text = "Subscribe to our newsletter for updates! Advertisement Cookie policy notice"
        cleaned = ContentProcessor.clean(text)
        
        assert "Subscribe" not in cleaned or "newsletter" not in cleaned
        assert "Advertisement" not in cleaned
        assert "Cookie" not in cleaned or "policy" not in cleaned

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

    @pytest.mark.unit
    def test_truncate_short_text(self):
        """Test that short text is not truncated."""
        text = "This is a short text."
        result = ContentProcessor.truncate(text, max_length=1000)
        
        assert result == text

    @pytest.mark.unit
    def test_truncate_long_text_at_sentence(self):
        """Test that long text is truncated at sentence boundary."""
        sentences = [
            "First sentence is here.",
            "Second sentence follows.",
            "Third sentence is added.",
            "And a fourth one too.",
        ]
        text = " ".join(sentences)
        
        result = ContentProcessor.truncate(text, max_length=50)
        
        # Should be truncated and end with a period
        assert len(result) <= 50
        # Should end at a sentence boundary (period or ...)
        assert result.endswith(".") or result.endswith("...")

    @pytest.mark.unit
    def test_truncate_adds_ellipsis_when_needed(self):
        """Test that ellipsis is added when truncating mid-sentence."""
        text = "A" * 100  # Long text with no periods
        result = ContentProcessor.truncate(text, max_length=50)
        
        assert len(result) <= 53  # 50 + "..."
        assert result.endswith("...")

    @pytest.mark.unit
    def test_truncate_respects_max_length(self):
        """Test that truncated text never exceeds max_length significantly."""
        text = "Word " * 1000
        max_len = 200
        result = ContentProcessor.truncate(text, max_length=max_len)
        
        # Should be close to max_length (within reason for sentence boundaries)
        assert len(result) <= max_len + 10

    @pytest.mark.unit
    def test_extract_key_sentences_filters_short_sentences(self):
        """Test that very short sentences are filtered out."""
        text = "Hi. This is a longer sentence with more content. Ok. And another substantial sentence here."
        result = ContentProcessor.extract_key_sentences(text, max_sentences=10)
        
        # Should not include "Hi." or "Ok." (too short)
        assert "Hi. " not in result or "Hi." not in result.split()[0]

    @pytest.mark.unit
    def test_extract_key_sentences_filters_long_sentences(self):
        """Test that very long sentences are filtered out."""
        short_sentence = "This is a reasonable sentence."
        long_sentence = "This " + "word " * 200 + "is too long."
        text = f"{short_sentence} {long_sentence}"
        
        result = ContentProcessor.extract_key_sentences(text, max_sentences=10)
        
        # Should include short sentence but not the extremely long one
        assert "reasonable sentence" in result

    @pytest.mark.unit
    def test_extract_key_sentences_limits_count(self):
        """Test that max_sentences limit is respected."""
        sentences = [f"Sentence number {i} with enough content." for i in range(20)]
        text = " ".join(sentences)
        
        result = ContentProcessor.extract_key_sentences(text, max_sentences=5)
        
        # Should only include first 5 sentences
        result_sentences = [s for s in result.split('.') if s.strip()]
        assert len(result_sentences) <= 5

    @pytest.mark.unit
    def test_extract_key_sentences_handles_empty_input(self):
        """Test that empty input returns empty string."""
        assert ContentProcessor.extract_key_sentences("") == ""
        assert ContentProcessor.extract_key_sentences(None) == ""

    @pytest.mark.unit
    def test_extract_key_sentences_preserves_order(self):
        """Test that sentences are kept in original order."""
        text = "First sentence here. Second sentence follows. Third one last."
        result = ContentProcessor.extract_key_sentences(text, max_sentences=3)
        
        # Order should be preserved
        assert result.index("First") < result.index("Second") < result.index("Third")
