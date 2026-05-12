"""Escalation logic for detecting when to route to human agents."""

from typing import Dict, Any, Optional, List, Tuple
import re
import json
import os
import logging

logger = logging.getLogger(__name__)


# Default escalation keywords (can be overridden by context/escalation_rules.json)
DEFAULT_ESCALATION_KEYWORDS = {
    "pricing": [
        "price", "pricing", "cost", "expensive", "cheap", "affordable",
        "budget", "payment", "pay", "charge", "fee", "subscription",
        "plan", "tier", "billing", "invoice", "refund", "money back"
    ],
    "refund": [
        "refund", "return", "money back", "cancel subscription",
        "cancel order", "reimburse", "compensation"
    ],
    "legal": [
        "lawyer", "attorney", "legal", "lawsuit", "sue", "court",
        "regulation", "compliance", "gdpr", "privacy policy", "terms",
        "contract", "agreement", "liability"
    ],
    "human_request": [
        "human", "agent", "representative", "person", "real person",
        "talk to someone", "speak to someone", "customer service",
        "support agent", "manager", "supervisor"
    ],
    "angry_indicators": [
        "angry", "frustrated", "disappointed", "unacceptable", "terrible",
        "awful", "horrible", "worst", "useless", "waste", "ridiculous",
        "outrageous", "disgusting", "appalled", "furious", "livid"
    ]
}


class EscalationDetector:
    """Detects when conversations should be escalated to human agents."""

    def __init__(self, escalation_rules_path: str = None):
        """
        Initialize escalation detector.

        Args:
            escalation_rules_path: Path to escalation rules JSON file
        """
        self.keywords = DEFAULT_ESCALATION_KEYWORDS.copy()
        self.sentiment_threshold = 0.3  # Escalate if sentiment < 0.3

        # Load custom rules if provided
        if escalation_rules_path and os.path.exists(escalation_rules_path):
            self._load_rules(escalation_rules_path)

    def _load_rules(self, path: str) -> None:
        """Load escalation rules from JSON file."""
        try:
            with open(path, 'r') as f:
                rules = json.load(f)

            if "keywords" in rules:
                self.keywords.update(rules["keywords"])

            if "sentiment_threshold" in rules:
                self.sentiment_threshold = rules["sentiment_threshold"]

            logger.info(f"Loaded escalation rules from {path}")

        except Exception as e:
            logger.error(f"Failed to load escalation rules: {e}")

    def detect_escalation(
        self,
        message: str,
        sentiment_score: Optional[float] = None
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Detect if message requires escalation.

        Args:
            message: Customer message text
            sentiment_score: Optional sentiment score (-1 to 1)

        Returns:
            Tuple of (escalation_required, reason, matched_keywords)
        """
        message_lower = message.lower()
        matched_keywords = []
        escalation_reasons = []

        # Check for explicit human request (highest priority)
        human_matches = self._find_keywords(message_lower, "human_request")
        if human_matches:
            matched_keywords.extend(human_matches)
            escalation_reasons.append("Customer explicitly requested human agent")

        # Check for pricing inquiries
        pricing_matches = self._find_keywords(message_lower, "pricing")
        if pricing_matches:
            matched_keywords.extend(pricing_matches)
            escalation_reasons.append("Pricing inquiry detected")

        # Check for refund requests
        refund_matches = self._find_keywords(message_lower, "refund")
        if refund_matches:
            matched_keywords.extend(refund_matches)
            escalation_reasons.append("Refund request detected")

        # Check for legal topics
        legal_matches = self._find_keywords(message_lower, "legal")
        if legal_matches:
            matched_keywords.extend(legal_matches)
            escalation_reasons.append("Legal/compliance topic detected")

        # Check sentiment score (only escalate for truly negative sentiment)
        # Threshold is -0.3, meaning scores below -0.3 trigger escalation
        # Neutral (0.0) and positive (>0.0) should NOT trigger escalation
        if sentiment_score is not None and sentiment_score < -self.sentiment_threshold:
            escalation_reasons.append(f"Negative sentiment detected (score: {sentiment_score})")

            # Also check for angry indicators
            angry_matches = self._find_keywords(message_lower, "angry_indicators")
            if angry_matches:
                matched_keywords.extend(angry_matches)

        # Remove duplicates
        matched_keywords = list(set(matched_keywords))

        # Determine if escalation is required
        escalation_required = len(escalation_reasons) > 0

        if escalation_required:
            reason = "; ".join(escalation_reasons)
            logger.info(f"Escalation detected: {reason} - Keywords: {matched_keywords}")
        else:
            reason = None

        return escalation_required, reason, matched_keywords

    def _find_keywords(
        self,
        text: str,
        category: str
    ) -> List[str]:
        """
        Find keywords from a category in text.

        Args:
            text: Text to search (lowercase)
            category: Keyword category

        Returns:
            List of matched keywords
        """
        if category not in self.keywords:
            return []

        matches = []
        for keyword in self.keywords[category]:
            # Use word boundary matching for better accuracy
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(keyword)

        return matches

    def get_escalation_email(
        self,
        category: str,
        priority: str
    ) -> str:
        """
        Get appropriate escalation email based on category and priority.

        Args:
            category: Escalation category
            priority: Ticket priority

        Returns:
            Email address for escalation
        """
        # Simple routing logic - customize based on your organization
        if category == "legal":
            return "legal@company.com"
        elif category == "refund" or category == "pricing":
            return "billing@company.com"
        elif priority in ["critical", "high"]:
            return "priority-support@company.com"
        else:
            return "support@company.com"


# Global escalation detector instance
# Try to load rules from context directory
escalation_detector = EscalationDetector(
    escalation_rules_path="context/escalation_rules.json"
)
