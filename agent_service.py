"""
Banking agent service with memory, adaptive behavior, and escalation.
"""

import json
import logging
import re
from typing import Dict, Tuple

from config import Config
from agent_rag import RAGAgent
from feedback_manager import FeedbackManager
from memory_manager import ConversationMemory

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(getattr(Config, 'SERVICE_LOG_FILE', 'agent_service.log'), mode='a')
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


class BankingAgentService:
    """Orchestrates LLM/RAG agent behavior with memory and feedback."""

    TRANSACTIONAL_KEYWORDS = [
        "transfer", "pay", "send money", "move money", "withdraw", "deposit",
        "approve", "authorize", "close account", "open account", "apply", "loan application",
        "cancel account", "dispute", "chargeback", "payment request"
    ]

    REGULATED_KEYWORDS = [
        "investment advice", "tax advice", "legal advice", "will", "estate planning",
        "securities", "underwriting", "regulated advice"
    ]

    PII_PATTERNS = [
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
        r"\b\d{16}\b",  # 16-digit card-number-like
        r"\b(?:\d{4}\s){3}\d{4}\b",  # spaced card number
        r"\b\d{10}\b"  # phone or account-like numeric string
    ]

    def __init__(self, strategy: str = "few-shot", use_rag: bool = True, memory_window: int = 3):
        self.agent = RAGAgent(strategy=strategy, use_rag=use_rag)
        self.memory = ConversationMemory(max_turns=memory_window)
        self.feedback = FeedbackManager(getattr(Config, 'FEEDBACK_LOG_FILE', 'feedback_log.json'))
        self.escalation_count = 0
        self.interaction_count = 0

    def _sanitize_input(self, user_input: str) -> Tuple[str, bool]:
        """Redact PII-like patterns and return whether PII was found."""
        clean = user_input
        found_pii = False
        for pattern in self.PII_PATTERNS:
            if re.search(pattern, clean):
                found_pii = True
                clean = re.sub(pattern, "[REDACTED]", clean)
        return clean, found_pii

    def _is_high_risk(self, user_input: str) -> Tuple[bool, str]:
        """Detect transactional or regulated requests that should be refused."""
        lower = user_input.lower()
        for keyword in self.TRANSACTIONAL_KEYWORDS:
            if keyword in lower:
                return True, f"Transactional request detected: {keyword}"
        for keyword in self.REGULATED_KEYWORDS:
            if keyword in lower:
                return True, f"Regulated advice request detected: {keyword}"
        if "account number" in lower or "social security" in lower:
            return True, "Sensitive personal identifier requested"
        return False, ""

    def _build_prompt(self, user_input: str) -> str:
        """Build an enhanced query that includes memory context."""
        context = self.memory.get_context() if Config.ENABLE_CONTEXT_MEMORY else ""
        if not context:
            return user_input
        return f"Prior conversation:\n{context}\n\nCurrent question: {user_input}"

    def process_query(self, user_input: str) -> Dict[str, str]:
        """Process a user query and return safe, contextual response metadata."""
        self.interaction_count += 1
        sanitized_input, contained_pii = self._sanitize_input(user_input)

        if contained_pii:
            logger.warning("PII detected and redacted from user input")
            return {
                "response": "I cannot process personal identifiers here. Please describe your question without account numbers, social security numbers, or other sensitive data.",
                "status": "pii_request",
                "escalation": "human_review" if contained_pii else "none"
            }

        reset_requested = self.memory.should_reset(sanitized_input)
        if reset_requested:
            self.memory.reset()
            return {
                "response": "I have cleared the previous context. Please ask your next question.",
                "status": "reset",
                "escalation": "none"
            }

        high_risk, reason = self._is_high_risk(sanitized_input)
        if high_risk:
            self.escalation_count += 1
            logger.info("Escalation triggered: %s", reason)
            return {
                "response": "I can only provide informational guidance. For transaction requests, approvals, or regulated advice, I will connect you with a human specialist.",
                "status": "escalated",
                "escalation": reason
            }

        prompt = self._build_prompt(sanitized_input)
        response, metadata = self.agent.process_query(prompt)

        self.memory.add_turn(sanitized_input, response)

        return {
            "response": response,
            "status": "answered",
            "escalation": "none",
            "metadata": metadata
        }

    def collect_feedback(self, query: str, response: str, rating: int, comments: str = "") -> Dict[str, str]:
        """Record explicit user feedback and return adaptive guidance."""
        rating = max(1, min(5, rating))
        self.feedback.record_feedback(query, response, rating, comments)
        recommendation = self.feedback.recommend_adjustment()
        logger.info("Feedback recorded with rating %d", rating)
        return {
            "feedback_count": self.feedback.get_summary()["count"],
            "summary": recommendation
        }


def interactive_service():
    """Run the banking agent service in interactive mode."""
    print("\n=== Banking Support Service ===")
    print("Type 'exit' to quit. Type 'reset' to clear conversation context.\n")
    service = BankingAgentService(strategy="few-shot", use_rag=True, memory_window=getattr(Config, 'MEMORY_WINDOW_SIZE', 3))

    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                break
            if not user_input:
                continue

            result = service.process_query(user_input)
            print(f"Agent: {result['response']}\n")

            if result["status"] == "answered":
                print("On a scale of 1-5, how helpful was this response? (Press Enter to skip)")
                rating_text = input("Rating: ").strip()
                if rating_text.isdigit():
                    rating = int(rating_text)
                    comments = input("Optional comment: ").strip()
                    feedback_result = service.collect_feedback(user_input, result['response'], rating, comments)
                    print(f"Feedback summary: {feedback_result['summary']}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!\n")
            break
        except Exception as exc:
            logger.error("Unexpected error in interactive service: %s", exc)
            print("An error occurred. Please try again later.\n")

    print("Session ended.")


if __name__ == "__main__":
    interactive_service()
