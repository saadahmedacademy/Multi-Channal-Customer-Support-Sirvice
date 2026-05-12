"""
Sentiment Threshold Boundary Tests.

Tests for sentiment threshold boundaries, edge cases, and escalation logic.
Validates the 0.3 threshold from the constitution.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ============== Threshold Boundary Tests ==============

class TestSentimentThreshold:
    """Tests for sentiment threshold boundaries per constitution (0.3)."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_escalation_at_threshold_boundary(self):
        """Test escalation at exactly -0.3 threshold."""
        from backend.worker.sentiment import sentiment_analyzer
        
        # Constitution says escalate when sentiment < 0.3 (meaning < -0.3)
        assert sentiment_analyzer.requires_escalation(-0.3) is False  # At threshold, no escalation
        assert sentiment_analyzer.requires_escalation(-0.31) is True  # Just below threshold

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_no_escalation_at_positive_threshold(self):
        """Test no escalation at positive threshold boundary."""
        from backend.worker.sentiment import sentiment_analyzer
        
        assert sentiment_analyzer.requires_escalation(0.3) is False
        assert sentiment_analyzer.requires_escalation(0.0) is False
        assert sentiment_analyzer.requires_escalation(0.5) is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_escalation_strong_negative(self):
        """Test escalation for strongly negative sentiment."""
        from backend.worker.sentiment import sentiment_analyzer
        
        assert sentiment_analyzer.requires_escalation(-0.5) is True
        assert sentiment_analyzer.requires_escalation(-0.7) is True
        assert sentiment_analyzer.requires_escalation(-0.9) is True
        assert sentiment_analyzer.requires_escalation(-1.0) is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_custom_threshold(self):
        """Test custom threshold override."""
        from backend.worker.sentiment import SentimentAnalyzer
        
        analyzer = SentimentAnalyzer()
        
        # More sensitive threshold (default is 0.3)
        assert analyzer.requires_escalation(-0.25, threshold=0.2) is True
        assert analyzer.requires_escalation(-0.15, threshold=0.2) is False
        
        # Less sensitive threshold
        assert analyzer.requires_escalation(-0.6, threshold=0.5) is True
        assert analyzer.requires_escalation(-0.45, threshold=0.5) is False


# ============== Escalation Detector Threshold Tests ==============

class TestEscalationDetectorThreshold:
    """Tests for escalation detector sentiment threshold."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_detector_default_threshold(self):
        """Test escalation detector uses default 0.3 threshold."""
        from backend.worker.escalation import EscalationDetector
        
        detector = EscalationDetector()
        
        # Should match constitution: threshold = 0.3
        assert detector.sentiment_threshold == 0.3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_detector_sentiment_just_below_threshold(self):
        """Test escalation when sentiment is just below -0.3."""
        from backend.worker.escalation import EscalationDetector
        
        detector = EscalationDetector()
        
        # -0.4 is below -0.3 threshold, should escalate
        requires, reason, keywords = detector.detect_escalation(
            "test message",
            sentiment_score=-0.4
        )
        
        assert requires is True
        assert "sentiment" in reason.lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_detector_sentiment_just_above_threshold(self):
        """Test no escalation when sentiment is just above -0.3."""
        from backend.worker.escalation import EscalationDetector
        
        detector = EscalationDetector()
        
        # -0.2 is above -0.3 threshold, should not escalate
        requires, reason, keywords = detector.detect_escalation(
            "test message",
            sentiment_score=-0.2
        )
        
        assert requires is False
        assert reason is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_detector_neutral_sentiment(self):
        """Test no escalation for neutral sentiment (0.0)."""
        from backend.worker.escalation import EscalationDetector
        
        detector = EscalationDetector()
        
        requires, reason, keywords = detector.detect_escalation(
            "I have a question",
            sentiment_score=0.0
        )
        
        assert requires is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_detector_positive_sentiment(self):
        """Test no escalation for positive sentiment."""
        from backend.worker.escalation import EscalationDetector
        
        detector = EscalationDetector()
        
        requires, reason, keywords = detector.detect_escalation(
            "This is great!",
            sentiment_score=0.7
        )
        
        assert requires is False


# ============== Sentiment Score Normalization Tests ==============

class TestSentimentNormalization:
    """Tests for sentiment score normalization to [-1, 1] range."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_score_normalized_to_range(self):
        """Test that scores are normalized to [-1, 1] range."""
        from backend.worker.sentiment import sentiment_analyzer
        
        # Very positive message
        result = sentiment_analyzer.analyze("excellent amazing wonderful fantastic great!")
        assert -1.0 <= result["score"] <= 1.0
        
        # Very negative message
        result = sentiment_analyzer.analyze("terrible awful horrible worst unacceptable!")
        assert -1.0 <= result["score"] <= 1.0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_score_precision(self):
        """Test that scores have appropriate precision."""
        from backend.worker.sentiment import sentiment_analyzer
        
        result = sentiment_analyzer.analyze("This is good")
        
        # Score should be rounded to 3 decimal places
        assert isinstance(result["score"], float)
        assert len(str(result["score"]).split('.')[-1]) <= 3


# ============== Keyword Sentiment Tests ==============

class TestKeywordSentiment:
    """Tests for keyword-based sentiment detection."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_positive_keywords_trigger_positive_sentiment(self):
        """Test that positive keywords result in positive score."""
        from backend.worker.sentiment import sentiment_analyzer
        
        positive_words = ["great", "excellent", "amazing", "wonderful", "fantastic"]
        
        for word in positive_words:
            result = sentiment_analyzer.analyze(f"This is {word}")
            assert result["score"] > 0, f"Expected positive score for '{word}', got {result['score']}"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_negative_keywords_trigger_negative_sentiment(self):
        """Test that negative keywords result in negative score."""
        from backend.worker.sentiment import sentiment_analyzer
        
        negative_words = ["terrible", "awful", "horrible", "worst", "unacceptable"]
        
        for word in negative_words:
            result = sentiment_analyzer.analyze(f"This is {word}")
            assert result["score"] < 0, f"Expected negative score for '{word}', got {result['score']}"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_intensifiers_amplify_sentiment(self):
        """Test that intensifiers amplify sentiment scores."""
        from backend.worker.sentiment import sentiment_analyzer
        
        # Positive with intensifier
        normal = sentiment_analyzer.analyze("good")
        intensified = sentiment_analyzer.analyze("very good")
        
        assert intensified["score"] > normal["score"]
        
        # Negative with intensifier
        normal_neg = sentiment_analyzer.analyze("bad")
        intensified_neg = sentiment_analyzer.analyze("very bad")
        
        assert intensified_neg["score"] < normal_neg["score"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_negation_reduces_sentiment(self):
        """Test that negation reduces sentiment."""
        from backend.worker.sentiment import sentiment_analyzer
        
        # Positive with negation
        positive = sentiment_analyzer.analyze("working")
        negated = sentiment_analyzer.analyze("not working")
        
        assert negated["score"] < positive["score"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_multiple_negators(self):
        """Test multiple negation words."""
        from backend.worker.sentiment import sentiment_analyzer
        
        result = sentiment_analyzer.analyze("I don't never not like this")
        
        # Should handle multiple negators gracefully
        assert "score" in result
        assert -1.0 <= result["score"] <= 1.0


# ============== Combined Sentiment + Escalation Tests ==============

class TestCombinedSentimentEscalation:
    """Tests for combined sentiment and escalation logic."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_escalation_very_angry_message(self):
        """Test escalation for very angry message with keywords."""
        from backend.worker.escalation import escalation_detector
        
        message = "This is absolutely terrible and unacceptable! I'm furious!"
        requires, reason, keywords = escalation_detector.detect_escalation(
            message,
            sentiment_score=-0.8
        )
        
        assert requires is True
        assert "sentiment" in reason.lower()
        assert len(keywords) > 0
        # Should detect angry indicators
        assert any(kw in keywords for kw in ["terrible", "unacceptable", "furious"])

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_no_escalation_mildly_negative_no_keywords(self):
        """Test no escalation for mildly negative message without keywords."""
        from backend.worker.escalation import escalation_detector
        
        # Sentiment just above threshold, no escalation keywords
        requires, reason, keywords = escalation_detector.detect_escalation(
            "I'm not completely satisfied with this",
            sentiment_score=-0.25
        )
        
        assert requires is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_escalation_pricing_and_negative_sentiment(self):
        """Test escalation for pricing inquiry with negative sentiment."""
        from backend.worker.escalation import escalation_detector
        
        message = "This is too expensive and a waste of money!"
        requires, reason, keywords = escalation_detector.detect_escalation(
            message,
            sentiment_score=-0.6
        )
        
        assert requires is True
        # Should detect both pricing and sentiment
        assert "Pricing" in reason or "sentiment" in reason.lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_escalation_human_request_overrides_sentiment(self):
        """Test that human request triggers escalation regardless of sentiment."""
        from backend.worker.escalation import escalation_detector
        
        # Polite request for human (positive sentiment but explicit human request)
        message = "Could you please connect me to a human agent? Thank you!"
        requires, reason, keywords = escalation_detector.detect_escalation(
            message,
            sentiment_score=0.5  # Positive sentiment
        )
        
        assert requires is True
        assert "human" in reason.lower()


# ============== Sentiment Label Classification Tests ==============

class TestSentimentLabels:
    """Tests for sentiment label classification."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_positive_label_threshold(self):
        """Test positive label requires score > 0.3."""
        from backend.worker.sentiment import sentiment_analyzer
        
        result = sentiment_analyzer.analyze("excellent amazing wonderful")
        assert result["label"] == "positive"
        assert result["score"] > 0.3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_negative_label_threshold(self):
        """Test negative label requires score < -0.3."""
        from backend.worker.sentiment import sentiment_analyzer
        
        result = sentiment_analyzer.analyze("terrible awful horrible")
        assert result["label"] == "negative"
        assert result["score"] < -0.3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_neutral_label_range(self):
        """Test neutral label for scores between -0.3 and 0.3."""
        from backend.worker.sentiment import sentiment_analyzer
        
        # Test various neutral messages
        neutral_messages = [
            "I have a question",
            "What are your hours?",
            "Need information about account",
            "Please help me"
        ]
        
        for msg in neutral_messages:
            result = sentiment_analyzer.analyze(msg)
            assert result["label"] == "neutral", f"Expected neutral for '{msg}', got {result['label']}"
            assert -0.3 <= result["score"] <= 0.3


# ============== Settings Threshold Tests ==============

class TestSettingsThreshold:
    """Tests that settings threshold matches constitution."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_settings_threshold_is_0_3(self):
        """Test that settings has 0.3 threshold per constitution."""
        from backend.config.settings import settings
        
        assert settings.escalation_sentiment_threshold == 0.3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_escalation_detector_uses_settings(self):
        """Test that escalation detector can use settings threshold."""
        from backend.config.settings import settings
        from backend.worker.escalation import EscalationDetector
        
        # Detector should be configurable
        detector = EscalationDetector()
        
        # Default should match constitution
        assert detector.sentiment_threshold == 0.3


# ============== Test Execution ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
