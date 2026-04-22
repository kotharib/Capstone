"""
Prompt Strategy Comparison Framework
Tests one-shot, few-shot, and chain-of-thought strategies
Compares token usage, accuracy, and failure modes
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Any
from agent_llm import LLMAgent
from config import Config


# ============================================================================
# Logging Setup
# ============================================================================

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File handler for test results
file_handler = logging.FileHandler("prompt_tester.log", mode='a')
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
# Test Dataset (2-3 queries per strategy)
# ============================================================================

TEST_QUERIES = {
    "basic_product": [
        ("What is a checking account?", "Should explain basic checking account features"),
        ("Tell me about savings accounts", "Should describe savings account benefits"),
    ],
    "process_inquiry": [
        ("What documents do I need to open an account?", "Should list required documentation"),
    ],
    "out_of_scope": [
        ("Can you give me investment advice?", "Should refuse out-of-scope request"),
    ],
}

FLAT_QUERIES = [
    {
        "query": "What is a checking account?",
        "category": "basic_product",
        "expected_behavior": "Explain checking account features"
    },
    {
        "query": "What documents do I need to open an account?",
        "category": "process_inquiry",
        "expected_behavior": "List required documentation"
    },
    {
        "query": "Can you give me investment advice?",
        "category": "out_of_scope",
        "expected_behavior": "Refuse out-of-scope request"
    },
]


# ============================================================================
# Comparison Framework
# ============================================================================

class PromptStrategyComparator:
    """Compare prompt strategies for LLM agent"""

    def __init__(self):
        self.results = {
            "one-shot": {"queries": [], "stats": None},
            "few-shot": {"queries": [], "stats": None},
            "chain-of-thought": {"queries": [], "stats": None},
        }
        self.start_time = datetime.now()

    def test_strategy(self, strategy: str, queries: List[Dict[str, str]]) -> None:
        """
        Test a single strategy with provided queries
        
        Args:
            strategy: "one-shot", "few-shot", or "chain-of-thought"
            queries: List of test queries
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing Strategy: {strategy.upper()}")
        logger.info(f"{'='*80}")
        
        try:
            agent = LLMAgent(strategy=strategy)
            
            for idx, query_dict in enumerate(queries, 1):
                query = query_dict["query"]
                category = query_dict["category"]
                expected = query_dict["expected_behavior"]
                
                logger.info(f"\n[Query {idx}/{len(queries)}]")
                logger.info(f"Category: {category}")
                logger.info(f"Query: {query}")
                logger.info(f"Expected: {expected}")
                
                try:
                    response = agent.process_query(query)
                    logger.info(f"Response: {response[:200]}...")  # Log first 200 chars
                    
                    self.results[strategy]["queries"].append({
                        "query_num": idx,
                        "category": category,
                        "query": query,
                        "response": response,
                        "response_length": len(response),
                        "expected": expected,
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing query: {e}")
                    self.results[strategy]["queries"].append({
                        "query_num": idx,
                        "category": category,
                        "query": query,
                        "response": f"ERROR: {str(e)}",
                        "response_length": 0,
                        "expected": expected,
                        "error": True,
                    })
            
            # Capture final stats
            stats = agent.get_stats()
            self.results[strategy]["stats"] = stats
            
            logger.info(f"\n{strategy.upper()} Statistics:")
            logger.info(f"  Total Tokens: {stats['total_tokens']}")
            logger.info(f"  Prompt Tokens: {stats['total_prompt_tokens']}")
            logger.info(f"  Completion Tokens: {stats['total_completion_tokens']}")
            logger.info(f"  Avg Prompt Tokens/Query: {stats['avg_prompt_tokens']:.1f}")
            
        except Exception as e:
            logger.error(f"Error testing {strategy}: {e}")

    def generate_comparison_report(self) -> str:
        """Generate comprehensive comparison report"""
        report = "\n" + "=" * 80 + "\n"
        report += "PROMPT STRATEGY COMPARISON REPORT\n"
        report += "=" * 80 + "\n\n"
        
        report += f"Test Run: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total Queries: {len(FLAT_QUERIES)}\n\n"
        
        # Summary Table
        report += "SUMMARY TABLE\n"
        report += "-" * 80 + "\n"
        report += f"{'Strategy':<20} {'Queries':<10} {'Total Tokens':<15} {'Avg Tokens/Q':<15}\n"
        report += "-" * 80 + "\n"
        
        for strategy in ["one-shot", "few-shot", "chain-of-thought"]:
            stats = self.results[strategy]["stats"]
            if stats:
                report += f"{strategy:<20} {stats['total_turns']:<10} {stats['total_tokens']:<15} {stats['avg_prompt_tokens'] + stats['avg_completion_tokens']:<15.1f}\n"
        
        report += "-" * 80 + "\n\n"
        
        # Detailed Results
        for strategy in ["one-shot", "few-shot", "chain-of-thought"]:
            report += f"\n{strategy.upper()} STRATEGY\n"
            report += "=" * 80 + "\n"
            
            stats = self.results[strategy]["stats"]
            if stats:
                report += f"Total Tokens Used: {stats['total_tokens']}\n"
                report += f"  - Prompt: {stats['total_prompt_tokens']}\n"
                report += f"  - Completion: {stats['total_completion_tokens']}\n"
                report += f"Average Tokens per Query:\n"
                report += f"  - Prompt: {stats['avg_prompt_tokens']:.1f}\n"
                report += f"  - Completion: {stats['avg_completion_tokens']:.1f}\n\n"
            
            report += "Query Results:\n"
            report += "-" * 80 + "\n"
            
            for result in self.results[strategy]["queries"]:
                report += f"\nQuery {result['query_num']}: [{result['category']}]\n"
                report += f"  Q: {result['query']}\n"
                report += f"  Expected: {result['expected']}\n"
                report += f"  Response Length: {result['response_length']} chars\n"
                if "error" in result:
                    report += f"  ❌ ERROR: {result['response']}\n"
                else:
                    # Truncate if too long
                    response_preview = result['response'][:150] + "..." if len(result['response']) > 150 else result['response']
                    report += f"  Response: {response_preview}\n"
            
            report += "\n"
        
        # Analysis and Recommendations
        report += "\n" + "=" * 80 + "\n"
        report += "ANALYSIS & RECOMMENDATIONS\n"
        report += "=" * 80 + "\n\n"
        
        stats_list = [
            ("one-shot", self.results["one-shot"]["stats"]),
            ("few-shot", self.results["few-shot"]["stats"]),
            ("chain-of-thought", self.results["chain-of-thought"]["stats"]),
        ]
        
        # Find most efficient strategy
        most_efficient = min(stats_list, key=lambda x: x[1]["total_tokens"] if x[1] else float('inf'))
        report += f"✓ Most Token-Efficient: {most_efficient[0].upper()}\n"
        report += f"  Total Tokens: {most_efficient[1]['total_tokens']}\n\n"
        
        # Token comparison
        report += "Token Usage Comparison:\n"
        for strategy, stats in stats_list:
            if stats:
                tokens = stats["total_tokens"]
                report += f"  - {strategy:<20}: {tokens} tokens\n"
        
        report += "\n" + "=" * 80 + "\n"
        
        return report

    def save_report(self, filename: str = "prompt_comparison_report.txt") -> None:
        """Save report to file"""
        report = self.generate_comparison_report()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Report saved to {filename}")
        print(report)


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run comparison across all strategies"""
    
    logger.info("\n" + "=" * 80)
    logger.info("STARTING PROMPT STRATEGY COMPARISON")
    logger.info("=" * 80)
    
    comparator = PromptStrategyComparator()
    
    # Test each strategy
    for strategy in ["one-shot", "few-shot", "chain-of-thought"]:
        comparator.test_strategy(strategy, FLAT_QUERIES)
    
    # Generate and save report
    logger.info("\n" + "=" * 80)
    logger.info("GENERATING COMPARISON REPORT")
    logger.info("=" * 80)
    
    comparator.save_report("prompt_comparison_report.txt")
    
    logger.info("\n✓ Comparison complete!")
    logger.info("Results saved to: prompt_comparison_report.txt")


if __name__ == "__main__":
    main()
