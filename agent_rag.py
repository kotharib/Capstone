"""
RAG-Enhanced LLM Agent
Combines LLM responses with retrieved documents from vector store
"""

import logging
import json
from typing import Tuple, Dict, Any, Optional
from datetime import datetime
from config import Config
from agent_llm import LLMAgent
from rag_system import RAGSystem

# ============================================================================
# Logging Setup
# ============================================================================

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("rag_agent.log", mode='a')
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


# ============================================================================
# RAG-Enhanced Agent
# ============================================================================

class RAGAgent:
    """
    LLM agent augmented with document retrieval
    Uses semantic search to find relevant documents before generating responses
    """
    
    def __init__(self, strategy: str = "few-shot", use_rag: bool = True, retrieval_top_k: int = 3):
        """
        Initialize RAG-enhanced agent
        
        Args:
            strategy: LLM prompt strategy ("one-shot", "few-shot", "chain-of-thought")
            use_rag: Whether to use retrieval augmentation
            retrieval_top_k: Number of documents to retrieve
        """
        self.strategy = strategy
        self.use_rag = use_rag
        self.retrieval_top_k = retrieval_top_k
        self.interaction_count = 0
        
        # Initialize components
        self.llm_agent = LLMAgent(strategy=strategy)
        self.rag_system = None
        
        if use_rag:
            logger.info("Initializing RAG system...")
            self.rag_system = RAGSystem()
            chunk_count = self.rag_system.ingest_documents()
            logger.info(f"RAG system ready with {chunk_count} document chunks")
        
        logger.info(f"RAGAgent initialized - Strategy: {strategy}, RAG: {use_rag}")
    
    def _get_rag_context(self, query: str) -> str:
        """
        Retrieve relevant context for query
        
        Args:
            query: User question
        
        Returns:
            Formatted context from retrieved documents
        """
        if not self.rag_system:
            return ""
        
        retrieved = self.rag_system.retrieve(query, top_k=self.retrieval_top_k)
        
        if not retrieved:
            logger.info(f"No relevant documents found for: {query[:50]}")
            return ""
        
        # Format context
        context = "\n".join([
            f"[{doc['source'].replace('_', ' ').title()}] {doc['content'][:400]}"
            for doc in retrieved
        ])
        
        logger.info(f"Retrieved {len(retrieved)} documents for context")
        return context
    
    def _build_rag_prompt(self, user_input: str, context: str) -> str:
        """
        Build prompt with retrieved context
        
        Args:
            user_input: User question
            context: Retrieved document context
        
        Returns:
            Enhanced prompt with context
        """
        prompt = f"""You are a helpful banking customer service assistant.
Use the provided context to answer questions accurately.
If the context doesn't contain relevant information, say so.
Keep responses under 150 words.

CONTEXT FROM KNOWLEDGE BASE:
{context}

Question: {user_input}
Answer:"""
        
        return prompt
    
    def process_query(self, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """
        Process query with optional RAG augmentation
        
        Args:
            user_input: User question
        
        Returns:
            Tuple of (response, metadata dict with retrieval info)
        """
        self.interaction_count += 1
        metadata = {
            "turn": self.interaction_count,
            "strategy": self.strategy,
            "use_rag": self.use_rag,
            "retrieved_docs": 0,
            "retrieval_time": 0
        }
        
        logger.info(f"[Turn {self.interaction_count}] User Input: {user_input}")
        
        try:
            # Step 1: Retrieve context if RAG enabled
            rag_context = ""
            if self.use_rag:
                import time
                start_time = time.time()
                
                retrieved = self.rag_system.retrieve(user_input, top_k=self.retrieval_top_k)
                metadata["retrieved_docs"] = len(retrieved)
                metadata["retrieval_time"] = time.time() - start_time
                
                if retrieved:
                    rag_context = self._get_rag_context(user_input)
                    logger.info(f"[Turn {self.interaction_count}] Retrieved {len(retrieved)} documents")
                    
                    # Store retrieved docs for comparison
                    metadata["retrieved"] = [
                        {
                            "source": doc["source"],
                            "similarity": doc["similarity"],
                            "content": doc["content"][:200]
                        }
                        for doc in retrieved
                    ]
            
            # Step 2: Generate response
            if self.use_rag and rag_context:
                # Use enhanced prompt with context
                rag_prompt = self._build_rag_prompt(user_input, rag_context)
                
                # Call LLM directly with enhanced prompt
                response = self.llm_agent.client.chat.completions.create(
                    model=Config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful banking assistant."},
                        {"role": "user", "content": rag_prompt}
                    ],
                    temperature=Config.LLM_TEMPERATURE,
                    max_tokens=Config.LLM_MAX_TOKENS,
                    timeout=Config.LLM_TIMEOUT
                )
                
                answer = response.choices[0].message.content.strip()
                
                # Track tokens
                metadata["prompt_tokens"] = response.usage.prompt_tokens
                metadata["completion_tokens"] = response.usage.completion_tokens
                metadata["total_tokens"] = response.usage.total_tokens
                
                logger.info(f"[Turn {self.interaction_count}] Response (with RAG): {answer[:100]}...")
                logger.info(f"[Turn {self.interaction_count}] Tokens - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}")
            else:
                # Use standard LLM agent
                answer = self.llm_agent.process_query(user_input)
                
                stats = self.llm_agent.get_stats()
                metadata["prompt_tokens"] = stats.get("avg_prompt_tokens", 0)
                metadata["completion_tokens"] = stats.get("avg_completion_tokens", 0)
                
                logger.info(f"[Turn {self.interaction_count}] Response (without RAG): {answer[:100]}...")
            
            return answer, metadata
        
        except Exception as e:
            logger.error(f"[Turn {self.interaction_count}] Error: {e}")
            return f"I encountered an error: {str(e)}", metadata
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "strategy": self.strategy,
            "use_rag": self.use_rag,
            "total_turns": self.interaction_count,
            "llm_stats": self.llm_agent.get_stats() if self.llm_agent else {}
        }


# ============================================================================
# Interactive Mode
# ============================================================================

def interactive_mode_with_rag(strategy: str = "few-shot", use_rag: bool = True):
    """
    Run RAG-enhanced agent in interactive mode
    
    Args:
        strategy: LLM prompt strategy
        use_rag: Whether to enable RAG
    """
    agent = RAGAgent(strategy=strategy, use_rag=use_rag)
    
    mode_label = f"{'RAG-Enhanced' if use_rag else 'LLM-Only'}"
    print("\n" + "=" * 80)
    print(f"Welcome to {Config.APP_NAME} ({mode_label} Mode)")
    print("=" * 80)
    print(f"Strategy: {strategy}")
    print(f"Retrieval Augmented Generation: {'Enabled' if use_rag else 'Disabled'}")
    print("Type 'exit', 'quit', or press Ctrl+C to end\n")
    
    turn_count = 0
    
    try:
        while turn_count < Config.MAX_CONVERSATION_TURNS:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print("Agent: Thank you for using our service. Goodbye!\n")
                    break
                
                if not user_input:
                    continue
                
                if len(user_input) > Config.MAX_INPUT_LENGTH:
                    print(f"Input too long (max {Config.MAX_INPUT_LENGTH} chars)\n")
                    continue
                
                turn_count += 1
                response, metadata = agent.process_query(user_input)
                
                # Display response
                print(f"Agent: {response}\n")
                
                # Optionally show retrieval info
                if use_rag and metadata.get("retrieved_docs", 0) > 0:
                    print(f"  [INFO: Retrieved {metadata['retrieved_docs']} documents in {metadata['retrieval_time']:.2f}s]\n")
                
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
    print(f"📊 Session Statistics ({mode_label}, {strategy}):")
    print(f"  Total Turns: {stats['total_turns']}")
    print(f"  RAG Enabled: {stats['use_rag']}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Default: RAG-enhanced with few-shot
    interactive_mode_with_rag(strategy="few-shot", use_rag=True)
