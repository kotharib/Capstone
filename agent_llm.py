"""
LLM-based Banking Agent with Multiple Prompt Strategies
Replaces keyword-matching with OpenAI LLM integration
Supports: One-shot, Few-shot, Chain-of-Thought strategies
"""

import logging
import json
from datetime import datetime
from typing import Tuple, Dict, Any
from config import Config

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("Please install openai: pip install openai")


# ============================================================================
# Logging Setup
# ============================================================================

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler(Config.LLM_LOG_FILE, mode='a')
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


# ============================================================================
# Banking Knowledge Base (for Prompts)
# ============================================================================

BANKING_PRODUCTS = {
    "checking": "A checking account is a transactional account for frequent deposits and withdrawals.",
    "savings": "A savings account earns interest and is designed for storing money long-term.",
    "credit_card": "A credit card allows you to borrow money for purchases and pay it back over time.",
    "overdraft": "Overdraft protection helps when you don't have enough funds to cover a transaction.",
}

BANKING_FAQS = {
    "open_account": "You can open an account in minutes online, by phone, or in person at our branches.",
    "documents": "You'll need a valid ID, proof of address, and Social Security number.",
    "insurance": "All deposits up to $250,000 are FDIC insured.",
}

OUT_OF_SCOPE = [
    "investment advice",
    "tax advice",
    "legal advice",
    "wire transfers",
    "account approval",
]


# ============================================================================
# LLM Agent with Prompt Strategies
# ============================================================================

class LLMAgent:
    """
    LLM-based agent supporting multiple prompt strategies
    """

    def __init__(self, strategy: str = "few-shot"):
        """
        Initialize LLM agent with specified strategy
        
        Args:
            strategy: "one-shot", "few-shot", or "chain-of-thought"
        """
        if strategy not in ["one-shot", "few-shot", "chain-of-thought"]:
            raise ValueError(f"Invalid strategy: {strategy}. Choose: one-shot, few-shot, chain-of-thought")
        
        self.strategy = strategy
        self.interaction_count = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_API_BASE,
            timeout=Config.LLM_TIMEOUT
        )
        
        logger.info(f"LLMAgent initialized with strategy: {strategy}")

    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM"""
        return """You are a helpful banking customer service assistant. 
Answer questions about banking products and services.
Stay professional, friendly, and concise.
Only discuss banking topics - refuse requests outside your scope.
Keep responses under 150 words."""

    def _build_one_shot_prompt(self, user_input: str) -> str:
        """One-shot strategy: Single example"""
        return f"""Banking Assistant Examples:

Q: What is a savings account?
A: A savings account earns interest and is designed for storing money long-term. You can earn competitive rates and withdraw funds when needed.

Q: {user_input}
A:"""

    def _build_few_shot_prompt(self, user_input: str) -> str:
        """Few-shot strategy: Multiple examples"""
        return f"""Banking Assistant Examples:

Q: What is a checking account?
A: A checking account is for frequent transactions. You get unlimited deposits, withdrawals, and often a debit card. No interest earned.

Q: What documents do I need to open an account?
A: You'll need a valid ID, proof of address, and Social Security number. The process takes just a few minutes.

Q: Are deposits insured?
A: Yes, all deposits up to $250,000 are FDIC insured for safety.

Q: {user_input}
A:"""

    def _build_chain_of_thought_prompt(self, user_input: str) -> str:
        """Chain-of-Thought strategy: Step-by-step reasoning"""
        return f"""Banking Assistant - Think step by step:

1. Understand the customer's question
2. Identify if it's about a banking product or service
3. Check if it's within scope (products, services, fees, documentation)
4. If out of scope, politely refuse and redirect
5. Provide accurate, helpful information

Customer question: {user_input}

Step 1 - Understanding the question:
[Think about what they're asking]

Step 2 - Is it about banking?
[Yes/No and category]

Step 3 - Is it in scope?
[Yes/No]

If in scope, provide a helpful, accurate answer:"""

    def _get_prompt_for_strategy(self, user_input: str) -> str:
        """Get appropriate prompt based on strategy"""
        if self.strategy == "one-shot":
            return self._build_one_shot_prompt(user_input)
        elif self.strategy == "few-shot":
            return self._build_few_shot_prompt(user_input)
        else:  # chain-of-thought
            return self._build_chain_of_thought_prompt(user_input)

    def process_query(self, user_input: str) -> str:
        """
        Process user query using LLM with selected strategy
        
        Returns:
            Response from LLM
        """
        self.interaction_count += 1
        
        try:
            # Build prompts
            system_prompt = self._build_system_prompt()
            user_prompt = self._get_prompt_for_strategy(user_input)
            
            logger.info(f"[Turn {self.interaction_count}] User Input: {user_input}")
            logger.info(f"[Turn {self.interaction_count}] Strategy: {self.strategy}")
            
            # Call LLM
            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=Config.LLM_TEMPERATURE,
                max_tokens=Config.LLM_MAX_TOKENS
            )
            
            # Extract response
            answer = response.choices[0].message.content.strip()
            
            # Track tokens
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            self.total_prompt_tokens += prompt_tokens
            self.total_completion_tokens += completion_tokens
            
            # Log response
            logger.info(f"[Turn {self.interaction_count}] Response: {answer}")
            logger.info(f"[Turn {self.interaction_count}] Tokens - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
            
            return answer
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(f"[Turn {self.interaction_count}] {error_msg}")
            return f"I encountered an error: {str(e)}"

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "strategy": self.strategy,
            "total_turns": self.interaction_count,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "avg_prompt_tokens": self.total_prompt_tokens / max(1, self.interaction_count),
            "avg_completion_tokens": self.total_completion_tokens / max(1, self.interaction_count),
        }


# ============================================================================
# Interactive Mode
# ============================================================================

def interactive_mode(strategy: str = "few-shot"):
    """
    Run LLM agent in interactive mode
    
    Args:
        strategy: "one-shot", "few-shot", or "chain-of-thought"
    """
    agent = LLMAgent(strategy=strategy)
    
    print("\n" + "=" * 80)
    print(f"Welcome to {Config.APP_NAME} (LLM Mode - {strategy})")
    print("=" * 80)
    print("Ask banking questions and see LLM responses")
    print("Type 'exit', 'quit', or press Ctrl+C to end\n")
    
    turn_count = 0
    
    try:
        while turn_count < Config.MAX_CONVERSATION_TURNS:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print("\nAgent: Thank you for using our service. Goodbye!\n")
                    break
                
                if not user_input:
                    continue
                
                if len(user_input) > Config.MAX_INPUT_LENGTH:
                    print(f"Input too long (max {Config.MAX_INPUT_LENGTH} chars)\n")
                    continue
                
                turn_count += 1
                response = agent.process_query(user_input)
                print(f"Agent: {response}\n")
                
            except KeyboardInterrupt:
                print("\nGoodbye!\n")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"An error occurred: {e}\n")
        
        if turn_count >= Config.MAX_CONVERSATION_TURNS:
            print(f"Maximum conversation turns ({Config.MAX_CONVERSATION_TURNS}) reached.\n")
    
    except Exception as e:
        logger.error(f"Error in interactive mode: {e}")
        print(f"Error: {e}\n")
    
    # Print statistics
    stats = agent.get_stats()
    print("=" * 80)
    print(f"📊 Session Statistics ({strategy}):")
    print(f"  Total Turns: {stats['total_turns']}")
    print(f"  Total Tokens: {stats['total_tokens']}")
    print(f"  Prompt Tokens: {stats['total_prompt_tokens']}")
    print(f"  Completion Tokens: {stats['total_completion_tokens']}")
    print(f"  Avg Prompt Tokens/Turn: {stats['avg_prompt_tokens']:.1f}")
    print(f"  Avg Completion Tokens/Turn: {stats['avg_completion_tokens']:.1f}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Default to few-shot
    interactive_mode(strategy="few-shot")
