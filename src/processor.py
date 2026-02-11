"""
Content processor — cleans and normalizes fetched content.
"""
import re
import logging

logger = logging.getLogger(__name__)


class ContentProcessor:
    """Processes raw web/article content into clean text."""

    @staticmethod
    def clean(text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        # Remove common web artifacts
        text = re.sub(r'Subscribe.*?newsletter', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Advertisement', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Cookie\s*(policy|consent|notice).*?\n', '', text, flags=re.IGNORECASE)
        # Remove URLs that aren't part of citations
        text = re.sub(r'https?://\S+', '', text)
        # Clean up
        text = text.strip()
        return text

    @staticmethod
    def truncate(text: str, max_length: int = 4000) -> str:
        """Truncate text to max length, breaking at sentence boundary."""
        if len(text) <= max_length:
            return text
        truncated = text[:max_length]
        # Try to break at last sentence
        last_period = truncated.rfind('.')
        if last_period > max_length * 0.7:
            return truncated[:last_period + 1]
        return truncated + "..."

    @staticmethod
    def extract_key_sentences(text: str, max_sentences: int = 10) -> str:
        """Extract the most informative sentences from text."""
        if not text:
            return ""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Filter out very short or very long sentences
        sentences = [s for s in sentences if 20 < len(s) < 500]
        return ' '.join(sentences[:max_sentences])
