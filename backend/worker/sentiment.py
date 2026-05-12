"""Sentiment analysis for customer messages."""

from typing import Dict, Any, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


# Sentiment keyword scores
POSITIVE_WORDS = {
    "great": 0.8, "good": 0.6, "excellent": 0.9, "amazing": 0.9,
    "wonderful": 0.8, "fantastic": 0.9, "love": 0.7, "helpful": 0.7,
    "thanks": 0.5, "thank": 0.5, "appreciate": 0.6, "happy": 0.7,
    "pleased": 0.7, "satisfied": 0.6, "perfect": 0.9, "awesome": 0.8,
    "resolved": 0.5, "fixed": 0.4, "working": 0.3
}

NEGATIVE_WORDS = {
    "bad": -0.6, "terrible": -0.9, "awful": -0.9, "horrible": -0.9,
    "worst": -0.9, "hate": -0.8, "angry": -0.7, "frustrated": -0.7,
    "disappointed": -0.6, "useless": -0.8, "waste": -0.7, "broken": -0.6,
    "not working": -0.7, "doesn't work": -0.7, "dont work": -0.7,
    "unacceptable": -0.8, "ridiculous": -0.7, "outrageous": -0.8,
    "furious": -0.9, "livid": -0.9, "appalled": -0.8, "disgusting": -0.9
}

INTENSIFIERS = {
    "very": 1.5, "really": 1.4, "extremely": 1.6, "absolutely": 1.5,
    "completely": 1.4, "totally": 1.4, "so": 1.3, "incredibly": 1.5
}

NEGATORS = {"not", "no", "never", "don't", "dont", "doesn't", "isn't", "aren't"}


class SentimentAnalyzer:
    """Simple keyword-based sentiment analyzer."""

    def __init__(self):
        self.positive_words = POSITIVE_WORDS
        self.negative_words = NEGATIVE_WORDS
        self.intensifiers = INTENSIFIERS
        self.negators = NEGATORS

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Dict with score, label, and details
        """
        text_lower = text.lower()
        words = text_lower.split()

        score = 0.0
        positive_matches = []
        negative_matches = []

        for i, word in enumerate(words):
            # Check for negation (look back 3 words)
            negated = False
            for j in range(max(0, i - 3), i):
                if words[j] in self.negators:
                    negated = True
                    break

            # Check for intensifier (look back 1 word)
            intensifier = 1.0
            if i > 0 and words[i - 1] in self.intensifiers:
                intensifier = self.intensifiers[words[i - 1]]

            # Check positive words
            if word in self.positive_words:
                word_score = self.positive_words[word] * intensifier
                if negated:
                    word_score *= -0.5  # Negation reduces but doesn't fully invert
                score += word_score
                positive_matches.append({"word": word, "score": word_score, "negated": negated})

            # Check negative words
            if word in self.negative_words:
                word_score = self.negative_words[word] * intensifier
                if negated:
                    word_score *= -0.5
                score += word_score
                negative_matches.append({"word": word, "score": word_score, "negated": negated})

        # Normalize score to -1 to 1 range
        normalized_score = max(-1.0, min(1.0, score / 5.0))

        # Determine label
        if normalized_score > 0.3:
            label = "positive"
        elif normalized_score < -0.3:
            label = "negative"
        else:
            label = "neutral"

        return {
            "score": round(normalized_score, 3),
            "label": label,
            "positive_matches": positive_matches,
            "negative_matches": negative_matches,
            "word_count": len(words)
        }

    def requires_escalation(self, score: float, threshold: float = 0.3) -> bool:
        """
        Check if sentiment score requires escalation.

        Args:
            score: Sentiment score (-1 to 1)
            threshold: Threshold for escalation

        Returns:
            True if escalation required
        """
        return score < -threshold


# Global sentiment analyzer instance
sentiment_analyzer = SentimentAnalyzer()


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Convenience function to analyze sentiment.

    Args:
        text: Text to analyze

    Returns:
        Sentiment analysis result
    """
    return sentiment_analyzer.analyze(text)
