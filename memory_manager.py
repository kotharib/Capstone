"""
Conversation memory manager for multi-turn banking assistant.
"""

import logging
from typing import List, Dict
from collections import deque

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Short-term conversation memory for agent context."""

    def __init__(self, max_turns: int = 3):
        self.max_turns = max_turns
        self.turns = deque(maxlen=max_turns)

    def add_turn(self, user_message: str, assistant_message: str) -> None:
        """Add a new conversation turn to memory."""
        self.turns.append({
            "user": user_message,
            "assistant": assistant_message
        })
        logger.debug("Added conversation turn to memory. Total turns: %d", len(self.turns))

    def get_context(self) -> str:
        """Get formatted recent conversation context."""
        if not self.turns:
            return ""

        entries = []
        for turn in self.turns:
            entries.append(f"Customer: {turn['user']}\nAssistant: {turn['assistant']}")

        context = "\n\n".join(entries)
        logger.debug("Built conversation context with %d turns", len(self.turns))
        return context

    def reset(self) -> None:
        """Clear the stored memory."""
        self.turns.clear()
        logger.info("Conversation memory reset")

    def should_reset(self, user_message: str) -> bool:
        """Decide whether the conversation should be reset."""
        reset_triggers = ["reset", "start over", "new topic", "clear context", "forget this"]
        lower_text = user_message.lower()
        if any(trigger in lower_text for trigger in reset_triggers):
            logger.info("Memory reset triggered by user message")
            return True
        return False

    def get_turn_count(self) -> int:
        """Return the number of turns currently in memory."""
        return len(self.turns)
