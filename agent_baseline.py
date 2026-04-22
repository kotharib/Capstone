"""
Baseline Banking AI Agent (V0)
Demonstrates simple rule-based response generation with clear limitations

This is intentionally basic to highlight why more sophisticated approaches are needed.
"""

import logging
from datetime import datetime
from typing import Tuple

# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent_baseline.log"),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Simple Rule-Based Response Templates
# ============================================================================

# Template 1: Keyword matching for product inquiries
PRODUCT_RESPONSES = {
    "checking account": "Our checking account includes: no monthly fee, debit card, online banking.",
    "savings account": "Our savings account offers: 0.45% APY, no minimum balance required.",
    "credit card": "Our credit card features: 1.5% cashback, no annual fee.",
    "overdraft": "Overdraft protection: $35 per occurrence, or link to savings for automatic transfer.",
}

# Template 2: FAQ-style responses
FAQ_RESPONSES = {
    "how long does account opening take": "Account opening typically takes 5-10 minutes online.",
    "what documents do i need": "You'll need: valid ID, social security number, current address.",
    "are my deposits insured": "Yes, deposits are FDIC insured up to $250,000.",
}

# Template 3: Refusal responses
REFUSAL_RESPONSES = {
    "transfer": "I cannot process transactions. Please log in to your account or speak with an agent.",
    "approve": "I cannot approve transactions. Please use online banking or contact support.",
    "wire": "I cannot process wire transfers. Please contact our branch or call customer service.",
    "legal advice": "I cannot provide legal advice. Please consult an attorney.",
    "investment advice": "I cannot provide investment advice. Please speak with a financial advisor.",
    "tax": "I cannot provide tax assistance. Please consult a tax professional.",
}

# ============================================================================
# Baseline Agent (V0)
# ============================================================================

class BaselineAgent:
    """
    Simple rule-based agent using keyword matching and templates
    """

    def __init__(self):
        """Initialize the agent"""
        self.interaction_count = 0
        logger.info("BaselineAgent initialized")

    def detect_intent(self, user_input: str) -> Tuple[str, str]:
        """
        Detect user intent using simple keyword matching
        
        Returns: (intent_type, matched_keyword)
        """
        user_lower = user_input.lower()

        # Check for refusal keywords (transactional/advice)
        for keyword in REFUSAL_RESPONSES.keys():
            if keyword in user_lower:
                return ("refusal", keyword)

        # Check for FAQ keywords
        for keyword in FAQ_RESPONSES.keys():
            if keyword in user_lower:
                return ("faq", keyword)

        # Check for product keywords
        for keyword in PRODUCT_RESPONSES.keys():
            if keyword in user_lower:
                return ("product_inquiry", keyword)

        # No match found
        return ("unknown", "")

    def generate_response(self, user_input: str) -> str:
        """
        Generate response based on intent and templates
        """
        intent, keyword = self.detect_intent(user_input)

        if intent == "refusal":
            response = REFUSAL_RESPONSES[keyword]
        elif intent == "faq":
            response = FAQ_RESPONSES[keyword]
        elif intent == "product_inquiry":
            response = PRODUCT_RESPONSES[keyword]
        else:
            # Fallback response
            response = "I'm not sure how to answer that. Please contact customer support."

        return response

    def process_query(self, user_input: str) -> str:
        """
        Process user query and return response
        """
        self.interaction_count += 1

        # Log input
        logger.info(f"[Turn {self.interaction_count}] User Input: {user_input}")

        # Detect intent
        intent, keyword = self.detect_intent(user_input)
        logger.info(f"[Turn {self.interaction_count}] Intent Detected: {intent} (keyword: {keyword})")

        # Generate response
        response = self.generate_response(user_input)
        logger.info(f"[Turn {self.interaction_count}] Response: {response}")

        return response


# ============================================================================
# Demonstration of Limitations
# ============================================================================

def demonstrate_limitations():
    """
    Show inherent limitations of rule-based agent
    """

    agent = BaselineAgent()

    print("\n" + "=" * 80)
    print("BASELINE AGENT DEMONSTRATION")
    print("=" * 80)

    # ========================================================================
    # LIMITATION 1: Keyword Order Sensitivity & Context Blindness
    # ========================================================================
    print("\n### LIMITATION 1: Keyword Order & Context Blindness ###\n")

    test_queries_limit1 = [
        ("What is overdraft protection?", "Works: Exact keyword match"),
        ("Tell me about overdraft", "Partial: No exact match"),
        ("I don't want overdraft protection", "Problem: Keyword present but negated"),
        ("Is overdraft included with checking account?", "Problem: Contains 'checking' & 'overdraft' but intent is unclear"),
    ]

    for query, explanation in test_queries_limit1:
        response = agent.process_query(query)
        print(f"❌ Query: {query}")
        print(f"   {explanation}")
        print(f"   Response: {response}\n")

    # ========================================================================
    # LIMITATION 2: No Context Memory & No Follow-up Understanding
    # ========================================================================
    print("\n### LIMITATION 2: No Context Memory & Follow-up Issues ###\n")

    conversation = [
        "Tell me about your checking account",
        "What about fees?",  # Ambiguous without prior context
        "Can I open one online?",  # Requires memory of "checking account"
    ]

    print("Conversation Flow (Agent has no memory of previous turns):\n")
    for query in conversation:
        response = agent.process_query(query)
        print(f"User: {query}")
        print(f"Agent: {response}\n")

    # ========================================================================
    # LIMITATION 3: Inability to Handle Paraphrasing or Synonyms
    # ========================================================================
    print("\n### LIMITATION 3: Paraphrasing & Synonyms Not Recognized ###\n")

    paraphrased_queries = [
        ("What products do you offer?", "No response (template doesn't match)"),
        ("Tell me about your savings option", "No response ('savings option' vs 'savings account')"),
        ("How do I move money between accounts?", "Blocked as 'transfer' (false positive refusal)"),
    ]

    for query, explanation in paraphrased_queries:
        response = agent.process_query(query)
        print(f"❌ Query: {query}")
        print(f"   Issue: {explanation}")
        print(f"   Response: {response}\n")

    # ========================================================================
    # LIMITATION 4: No Confidence Scoring or Uncertainty Handling
    # ========================================================================
    print("\n### LIMITATION 4: False Positives & No Confidence Scoring ###\n")

    false_positive_queries = [
        (
            "What is the legal framework for banking?",
            "Problem: Contains 'legal' → triggers legal advice refusal (false positive)"
        ),
        (
            "I heard about tax-deferred savings. Can you explain?",
            "Problem: Contains 'tax' → triggers tax advice refusal (false positive)"
        ),
    ]

    for query, issue in false_positive_queries:
        response = agent.process_query(query)
        print(f"❌ Query: {query}")
        print(f"   {issue}")
        print(f"   Response: {response}\n")

    print("\n" + "=" * 80)


# ============================================================================
# Why This Is Insufficient for Real Users
# ============================================================================

def explain_insufficiency():
    """
    Explain why rule-based agents fail in production
    """

    print("\n" + "=" * 80)
    print("WHY THIS BASELINE IS INSUFFICIENT FOR REAL USERS")
    print("=" * 80 + "\n")

    limitations = {
        "1. No Language Understanding": [
            "- Cannot interpret intent from paraphrased queries",
            "- Fails on synonyms ('savings option' vs 'savings account')",
            "- No semantic understanding of meaning",
            "- Result: Users get 'I'm not sure' for valid questions",
        ],
        "2. No Context or Memory": [
            "- Every query treated independently",
            "- Cannot answer follow-up questions ('What about fees?' requires prior context)",
            "- No multi-turn conversation ability",
            "- Result: Frustrating, repetitive conversations",
        ],
        "3. False Positives & Over-Blocking": [
            "- Keyword 'tax' blocks informational queries about tax-deferred products",
            "- Keyword 'legal' blocks regulatory framework questions",
            "- No confidence scoring or nuance",
            "- Result: Users blocked from legitimate questions",
        ],
        "4. No Nuance or Context-Awareness": [
            "- Cannot distinguish 'I don't want overdraft' from 'Tell me about overdraft'",
            "- Cannot understand rhetorical vs literal questions",
            "- No ability to reason about user intent",
            "- Result: Wrong answers or refusing legitimate requests",
        ],
        "5. No Escalation Logic": [
            "- All uncertain queries get generic fallback",
            "- No ability to detect when human should take over",
            "- No confidence metric to trigger escalation",
            "- Result: Missed opportunities for specialist intervention",
        ],
        "6. Impossible to Scale": [
            "- Adding 1000 products = 1000 manual templates",
            "- Adding variations = combinatorial explosion",
            "- No learning or adaptation from user interactions",
            "- Result: Maintenance nightmare, cannot handle real banking diversity",
        ],
    }

    for category, details in limitations.items():
        print(f"\n{category}")
        for detail in details:
            print(f"  {detail}")

    print("\n" + "=" * 80)
    print("NEXT STEPS: Use LLM-based retrieval-augmented generation (RAG) with:")
    print("  ✓ Language understanding (semantic meaning, not keyword matching)")
    print("  ✓ Context memory (conversation history)")
    print("  ✓ Confidence scoring (escalate uncertain queries)")
    print("  ✓ Source grounding (cite policy documents)")
    print("  ✓ Safety guardrails (explicit boundaries)")
    print("=" * 80 + "\n")


# ============================================================================
# Interactive Mode
# ============================================================================

def interactive_mode():
    """
    Accept user input interactively and process through agent
    """
    from config import Config
    
    agent = BaselineAgent()
    
    print("\n" + "=" * 80)
    print(f"Welcome to {Config.APP_NAME}")
    print("=" * 80)
    print("Interactive Mode - Ask banking questions and see how the agent responds")
    print("Type 'exit', 'quit', or press Ctrl+C to end conversation\n")
    
    turn_count = 0
    
    try:
        while turn_count < Config.MAX_CONVERSATION_TURNS:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                # Check exit conditions
                if user_input.lower() in ['exit', 'quit']:
                    print("Agent: Goodbye! Thank you for using our service.\n")
                    break
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Check input length
                if len(user_input) > Config.MAX_INPUT_LENGTH:
                    print(f"Agent: Input too long (maximum {Config.MAX_INPUT_LENGTH} characters). Please try again.\n")
                    continue
                
                # Process query
                turn_count += 1
                response = agent.process_query(user_input)
                print(f"Agent: {response}\n")
                
            except KeyboardInterrupt:
                print("\nAgent: Goodbye!\n")
                break
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                print("Agent: An error occurred. Please try again.\n")
        
        if turn_count >= Config.MAX_CONVERSATION_TURNS:
            print(f"Agent: Maximum conversation turns ({Config.MAX_CONVERSATION_TURNS}) reached. Goodbye!\n")
    
    except Exception as e:
        logger.error(f"Error in interactive mode: {e}")
        print(f"An error occurred: {e}\n")
    
    print("=" * 80)
    print(f"📊 Log file saved to: {Config.LOG_FILE}")
    print("=" * 80 + "\n")


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    interactive_mode()
