"""Unit tests for escalation logic."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.worker.escalation import EscalationDetector


@pytest.fixture
def detector():
    """Create escalation detector instance for testing."""
    return EscalationDetector()


class TestEscalationKeywordDetection:
    """Test keyword-based escalation detection."""

    def test_escalate_on_pricing_keywords(self, detector):
        """Test that pricing keywords trigger escalation."""
        messages = [
            "What is your pricing?",
            "How much does it cost?",
            "This is too expensive"
        ]

        for message in messages:
            escalated, reason, keywords = detector.detect_escalation(message)
            assert escalated is True, f"Should escalate: {message}"
            assert "Pricing" in reason

    def test_escalate_on_refund_keywords(self, detector):
        """Test that refund keywords trigger escalation."""
        messages = [
            "I want a refund",
            "Can I get my money back?",
            "I need to cancel my subscription",
        ]

        for message in messages:
            escalated, reason, keywords = detector.detect_escalation(message)
            assert escalated is True, f"Should escalate: {message}"

    def test_escalate_on_legal_keywords(self, detector):
        """Test that legal keywords trigger escalation."""
        messages = [
            "I'm going to sue you",
            "My lawyer will contact you",
            "You violated GDPR",
        ]

        for message in messages:
            escalated, reason, keywords = detector.detect_escalation(message)
            assert escalated is True, f"Should escalate: {message}"

    def test_escalate_on_explicit_human_request(self, detector):
        """Test that explicit human requests trigger escalation."""
        messages = [
            "I want to speak to a human",
            "Can I talk to an agent?",
            "I need a real person",
        ]

        for message in messages:
            escalated, reason, keywords = detector.detect_escalation(message)
            assert escalated is True, f"Should escalate: {message}"

    def test_no_escalation_for_normal_messages(self, detector):
        """Test that normal messages don't trigger escalation."""
        messages = [
            "How do I reset my password?",
            "What are your business hours?",
            "Can you explain this feature?",
        ]

        for message in messages:
            escalated, reason, keywords = detector.detect_escalation(message)
            assert escalated is False, f"Should not escalate: {message}"


class TestEscalationCaseInsensitivity:
    """Test that escalation is case-insensitive."""

    def test_escalate_uppercase_keywords(self, detector):
        """Test that uppercase keywords trigger escalation."""
        messages = [
            "WHAT IS YOUR PRICING?",
            "I WANT A REFUND",
            "I'LL SUE YOU",
        ]

        for message in messages:
            escalated, reason, keywords = detector.detect_escalation(message)
            assert escalated is True, f"Should escalate: {message}"

    def test_escalate_mixed_case_keywords(self, detector):
        """Test that mixed case keywords trigger escalation."""
        messages = [
            "What Is Your PrIcInG?",
            "I WaNt A ReFuNd",
            "I'll SuE yOu",
        ]

        for message in messages:
            escalated, reason, keywords = detector.detect_escalation(message)
            assert escalated is True, f"Should escalate: {message}"


class TestEscalationWithSentiment:
    """Test escalation combined with sentiment analysis."""

    def test_escalate_on_negative_sentiment_with_keywords(self, detector):
        """Test that negative sentiment + keywords trigger escalation."""
        message = "I'm very angry about your pricing!"
        escalated, reason, keywords = detector.detect_escalation(
            message, sentiment_score=-0.8
        )
        assert escalated is True

    def test_escalate_on_very_negative_sentiment_alone(self, detector):
        """Test that very negative sentiment alone can trigger escalation."""
        message = "I'm extremely frustrated and angry with your service!"
        escalated, reason, keywords = detector.detect_escalation(
            message, sentiment_score=-0.9
        )
        assert escalated is True

    def test_no_escalation_on_positive_sentiment(self, detector):
        """Test that positive sentiment doesn't trigger escalation."""
        message = "I love your service, it's great!"
        escalated, reason, keywords = detector.detect_escalation(
            message, sentiment_score=0.8
        )
        assert escalated is False


class TestEscalationEdgeCases:
    """Test edge cases in escalation logic."""

    def test_escalate_empty_message(self, detector):
        """Test handling of empty message."""
        escalated, reason, keywords = detector.detect_escalation("")
        assert escalated is False

    def test_escalate_very_long_message(self, detector):
        """Test handling of very long message."""
        long_message = "normal text " * 1000 + " I want a refund"
        escalated, reason, keywords = detector.detect_escalation(long_message)
        assert escalated is True

    def test_escalate_with_special_characters(self, detector):
        """Test handling of special characters."""
        message = "I want a refund!!! @#$%"
        escalated, reason, keywords = detector.detect_escalation(message)
        assert escalated is True

    def test_escalate_with_unicode(self, detector):
        """Test handling of Unicode characters."""
        message = "I want a refund 💰"
        escalated, reason, keywords = detector.detect_escalation(message)
        assert escalated is True


class TestEscalationWordBoundaries:
    """Test that escalation respects word boundaries."""

    def test_no_escalation_for_partial_matches(self, detector):
        """Test that partial word matches don't trigger escalation."""
        messages = [
            "This feature is priceless",
            "I appreciate your help",
        ]

        for message in messages:
            escalated, reason, keywords = detector.detect_escalation(message)
            assert escalated is False, f"Should not escalate: {message}"


class TestEscalationEmailRouting:
    """Test escalation email routing."""

    def test_legal_category_email(self, detector):
        """Test that legal category routes to legal email."""
        email = detector.get_escalation_email("legal", "high")
        assert "legal" in email

    def test_billing_category_email(self, detector):
        """Test that refund/pricing routes to billing email."""
        email = detector.get_escalation_email("refund", "normal")
        assert "billing" in email

    def test_critical_priority_email(self, detector):
        """Test that critical priority routes correctly."""
        email = detector.get_escalation_email("general", "critical")
        assert "priority-support" in email


class TestEscalationDetectorInitialization:
    """Test escalation detector initialization."""

    def test_default_keywords_loaded(self, detector):
        """Test that default keywords are loaded."""
        assert "pricing" in detector.keywords
        assert "refund" in detector.keywords
        assert "legal" in detector.keywords
        assert "human_request" in detector.keywords
        assert "angry_indicators" in detector.keywords

    def test_default_sentiment_threshold(self, detector):
        """Test default sentiment threshold."""
        assert detector.sentiment_threshold == 0.3
