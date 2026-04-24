"""
Feedback manager for adaptive banking assistant behavior.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class FeedbackManager:
    """Store and summarize user feedback for adaptive behavior."""

    def __init__(self, feedback_file: str = "feedback_log.json"):
        self.feedback_file = Path(feedback_file)
        self.feedback: List[Dict[str, Any]] = []
        self.load_feedback()

    def load_feedback(self) -> None:
        """Load feedback records from disk."""
        if self.feedback_file.exists():
            try:
                self.feedback = json.loads(self.feedback_file.read_text())
            except Exception as exc:
                logger.warning("Could not load feedback file: %s", exc)
                self.feedback = []
        else:
            self.feedback = []

    def record_feedback(self, query: str, response: str, rating: int, comments: str = "") -> None:
        """Record user feedback."""
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "query": query,
            "response": response,
            "rating": rating,
            "comments": comments.strip()
        }
        self.feedback.append(record)
        self._persist()
        logger.info("Recorded feedback rating=%d for query: %s", rating, query[:80])

    def _persist(self) -> None:
        """Persist feedback to disk."""
        try:
            self.feedback_file.write_text(json.dumps(self.feedback, indent=2))
        except Exception as exc:
            logger.error("Failed to persist feedback file: %s", exc)

    def get_summary(self) -> Dict[str, Any]:
        """Return feedback summary statistics."""
        if not self.feedback:
            return {"count": 0, "average_rating": None, "low_ratings": 0}

        total = sum(item["rating"] for item in self.feedback)
        average = total / len(self.feedback)
        low_ratings = sum(1 for item in self.feedback if item["rating"] <= 2)
        return {
            "count": len(self.feedback),
            "average_rating": average,
            "low_ratings": low_ratings
        }

    def recommend_adjustment(self) -> str:
        """Generate a simple adaptation recommendation."""
        summary = self.get_summary()
        if summary["count"] == 0:
            return "No feedback yet. Continue monitoring user ratings."

        if summary["average_rating"] <= 2.5:
            return "Average feedback is low. Simplify answers and reinforce safety boundaries."
        elif summary["average_rating"] <= 3.5:
            return "Moderate feedback. Keep responses concise and clarify scope."
        return "Feedback is positive. Maintain current response style and safety guardrails."
