"""
RAG Comparison Framework
Tests responses with and without retrieval augmentation
Measures improvements in accuracy, relevance, and token usage
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from agent_llm import LLMAgent
from agent_rag import RAGAgent

# ============================================================================
# Logging Setup
# ============================================================================

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("rag_comparison.log", mode='a')
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
# Test Dataset
# ============================================================================

TEST_QUERIES = [
    {
        "query": "What documents do I need to open a bank account?",
        "category": "process_inquiry",
        "expected_keywords": ["id", "social security", "proof of address"],
        "complexity": "medium"
    },
    {
        "query": "How is my money protected at your bank?",
        "category": "safety_inquiry",
        "expected_keywords": ["fdic", "250000", "insured"],
        "complexity": "high"
    },
    {
        "query": "What are the fees for checking accounts?",
        "category": "fee_inquiry",
        "expected_keywords": ["monthly", "maintenance", "overdraft"],
        "complexity": "medium"
    },
    {
        "query": "What is overdraft protection and how does it work?",
        "category": "product_feature",
        "expected_keywords": ["overdraft", "protection", "linked account", "fee"],
        "complexity": "high"
    },
    {
        "query": "Can I get a personal loan and what are the rates?",
        "category": "loan_inquiry",
        "expected_keywords": ["loan", "apr", "credit", "term"],
        "complexity": "high"
    },
]


# ============================================================================
# Comparison Framework
# ============================================================================

class RAGComparator:
    """Compare LLM responses with and without retrieval augmentation"""
    
    def __init__(self):
        self.results = {
            "without_rag": {"queries": [], "stats": None},
            "with_rag": {"queries": [], "stats": None},
        }
        self.start_time = datetime.now()
    
    def evaluate_response(self, response: str, expected_keywords: List[str]) -> Dict[str, Any]:
        """
        Evaluate response quality
        
        Args:
            response: Generated response
            expected_keywords: Keywords that should appear
        
        Returns:
            Evaluation metrics
        """
        response_lower = response.lower()
        
        keywords_found = sum(1 for kw in expected_keywords if kw.lower() in response_lower)
        keyword_coverage = keywords_found / len(expected_keywords) if expected_keywords else 0
        
        return {
            "response_length": len(response),
            "keywords_found": keywords_found,
            "total_keywords": len(expected_keywords),
            "keyword_coverage": keyword_coverage,
            "contains_all_keywords": keywords_found == len(expected_keywords)
        }
    
    def test_mode(self, mode: str, queries: List[Dict[str, Any]]) -> None:
        """
        Test a specific mode (with/without RAG)
        
        Args:
            mode: "without_rag" or "with_rag"
            queries: List of test queries
        """
        use_rag = mode == "with_rag"
        mode_name = "RAG-Enhanced" if use_rag else "LLM-Only"
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing Mode: {mode_name}")
        logger.info(f"{'='*80}")
        
        agent = RAGAgent(strategy="few-shot", use_rag=use_rag)
        
        for idx, query_dict in enumerate(queries, 1):
            query = query_dict["query"]
            category = query_dict["category"]
            expected_keywords = query_dict["expected_keywords"]
            
            logger.info(f"\n[Query {idx}/{len(queries)}] ({category})")
            logger.info(f"Q: {query}")
            
            try:
                response, metadata = agent.process_query(query)
                
                # Evaluate response
                evaluation = self.evaluate_response(response, expected_keywords)
                
                # Store result
                result = {
                    "query_num": idx,
                    "category": category,
                    "query": query,
                    "response": response[:300] + "..." if len(response) > 300 else response,
                    "response_length": len(response),
                    "evaluation": evaluation,
                    "metadata": {
                        "tokens": metadata.get("total_tokens", 0),
                        "retrieved_docs": metadata.get("retrieved_docs", 0),
                        "retrieval_time": metadata.get("retrieval_time", 0),
                    }
                }
                
                # Add retrieved docs if RAG
                if use_rag and metadata.get("retrieved"):
                    result["retrieved_context"] = [
                        {
                            "source": doc["source"],
                            "similarity": doc["similarity"]
                        }
                        for doc in metadata["retrieved"]
                    ]
                
                self.results[mode]["queries"].append(result)
                
                # Log evaluation
                logger.info(f"A: {response[:100]}...")
                logger.info(f"  Keyword Coverage: {evaluation['keyword_coverage']:.1%} ({evaluation['keywords_found']}/{evaluation['total_keywords']})")
                logger.info(f"  Response Length: {evaluation['response_length']} chars")
                logger.info(f"  Tokens Used: {metadata.get('total_tokens', 'N/A')}")
                
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                self.results[mode]["queries"].append({
                    "query_num": idx,
                    "category": category,
                    "query": query,
                    "error": str(e),
                    "response": f"ERROR: {str(e)}"
                })
    
    def generate_report(self) -> str:
        """Generate comprehensive comparison report"""
        
        without_rag = self.results["without_rag"]["queries"]
        with_rag = self.results["with_rag"]["queries"]
        
        report = "\n" + "=" * 80 + "\n"
        report += "RAG COMPARISON REPORT\n"
        report += "=" * 80 + "\n\n"
        
        report += f"Test Run: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total Queries: {len(without_rag)}\n\n"
        
        # Summary Table
        report += "SUMMARY COMPARISON\n"
        report += "-" * 80 + "\n"
        
        # Calculate metrics
        metrics_without = self._calculate_metrics(without_rag)
        metrics_with = self._calculate_metrics(with_rag)
        
        report += f"{'Metric':<30} {'LLM-Only':<20} {'RAG-Enhanced':<20} {'Improvement':<10}\n"
        report += "-" * 80 + "\n"
        
        # Keyword coverage
        coverage_without = metrics_without["avg_keyword_coverage"]
        coverage_with = metrics_with["avg_keyword_coverage"]
        improvement = ((coverage_with - coverage_without) / coverage_without * 100) if coverage_without > 0 else 0
        report += f"{'Avg Keyword Coverage':<30} {coverage_without:<20.1%} {coverage_with:<20.1%} {improvement:+.1f}%\n"
        
        # Response length
        len_without = metrics_without["avg_response_length"]
        len_with = metrics_with["avg_response_length"]
        improvement = ((len_with - len_without) / len_without * 100) if len_without > 0 else 0
        report += f"{'Avg Response Length':<30} {len_without:<20.0f} {len_with:<20.0f} {improvement:+.1f}%\n"
        
        # Token usage
        tokens_without = metrics_without["avg_tokens"]
        tokens_with = metrics_with["avg_tokens"]
        improvement = ((tokens_with - tokens_without) / tokens_without * 100) if tokens_without > 0 else 0
        report += f"{'Avg Tokens per Query':<30} {tokens_without:<20.1f} {tokens_with:<20.1f} {improvement:+.1f}%\n"
        
        report += "-" * 80 + "\n\n"
        
        # Detailed Results
        report += "DETAILED RESULTS\n"
        report += "=" * 80 + "\n\n"
        
        report += "WITHOUT RAG (LLM-Only)\n"
        report += "-" * 80 + "\n"
        for result in without_rag:
            if "error" in result:
                report += f"Query {result['query_num']}: ERROR - {result['error']}\n"
            else:
                report += f"Query {result['query_num']}: {result['query'][:60]}\n"
                report += f"  Keywords: {result['evaluation']['keywords_found']}/{result['evaluation']['total_keywords']}\n"
                report += f"  Response: {result['response'][:100]}...\n\n"
        
        report += "\nWITH RAG (RAG-Enhanced)\n"
        report += "-" * 80 + "\n"
        for result in with_rag:
            if "error" in result:
                report += f"Query {result['query_num']}: ERROR - {result['error']}\n"
            else:
                report += f"Query {result['query_num']}: {result['query'][:60]}\n"
                report += f"  Keywords: {result['evaluation']['keywords_found']}/{result['evaluation']['total_keywords']}\n"
                report += f"  Retrieved Docs: {result['metadata']['retrieved_docs']}\n"
                report += f"  Response: {result['response'][:100]}...\n\n"
        
        # Analysis
        report += "\n" + "=" * 80 + "\n"
        report += "ANALYSIS & INSIGHTS\n"
        report += "=" * 80 + "\n\n"
        
        report += "Key Findings:\n"
        
        # Calculate success rate
        success_without = sum(1 for r in without_rag if r['evaluation']['contains_all_keywords']) / len(without_rag) if without_rag else 0
        success_with = sum(1 for r in with_rag if r['evaluation']['contains_all_keywords']) / len(with_rag) if with_rag else 0
        
        report += f"✓ Response Completeness:\n"
        report += f"  - LLM-Only: {success_without:.1%} of queries contained all expected keywords\n"
        report += f"  - RAG-Enhanced: {success_with:.1%} of queries contained all expected keywords\n"
        report += f"  - Improvement: {(success_with - success_without):.1%}\n\n"
        
        report += f"✓ Context Awareness:\n"
        report += f"  - RAG system retrieved an average of {metrics_with['avg_retrieved_docs']:.1f} documents per query\n"
        report += f"  - Average retrieval time: {metrics_with['avg_retrieval_time']*1000:.1f}ms\n\n"
        
        report += f"✓ Token Efficiency:\n"
        report += f"  - LLM-Only average: {tokens_without:.1f} tokens\n"
        report += f"  - RAG-Enhanced average: {tokens_with:.1f} tokens\n"
        if tokens_with > tokens_without:
            report += f"  - Trade-off: +{(tokens_with - tokens_without):.1f} tokens for improved accuracy\n\n"
        else:
            report += f"  - Benefit: -{abs(tokens_with - tokens_without):.1f} tokens with improved accuracy\n\n"
        
        # Missing context analysis
        report += "✓ Missing Context Scenarios:\n"
        missing_count_without = sum(1 for r in without_rag if not r['evaluation']['contains_all_keywords'])
        missing_count_with = sum(1 for r in with_rag if not r['evaluation']['contains_all_keywords'])
        
        report += f"  - Queries missing context: LLM-Only ({missing_count_without}), RAG-Enhanced ({missing_count_with})\n"
        if missing_count_with < missing_count_without:
            report += f"  - Reduction: {missing_count_without - missing_count_with} fewer incomplete responses with RAG\n\n"
        
        report += "\n" + "=" * 80 + "\n"
        
        return report
    
    def _calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate aggregate metrics from results"""
        valid_results = [r for r in results if "error" not in r]
        
        if not valid_results:
            return {
                "avg_keyword_coverage": 0,
                "avg_response_length": 0,
                "avg_tokens": 0,
                "avg_retrieved_docs": 0,
                "avg_retrieval_time": 0,
            }
        
        return {
            "avg_keyword_coverage": sum(r['evaluation']['keyword_coverage'] for r in valid_results) / len(valid_results),
            "avg_response_length": sum(r['response_length'] for r in valid_results) / len(valid_results),
            "avg_tokens": sum(r['metadata']['tokens'] for r in valid_results) / len(valid_results),
            "avg_retrieved_docs": sum(r['metadata']['retrieved_docs'] for r in valid_results) / len(valid_results),
            "avg_retrieval_time": sum(r['metadata']['retrieval_time'] for r in valid_results) / len(valid_results),
        }
    
    def save_report(self, filename: str = "rag_comparison_report.txt") -> None:
        """Save report to file"""
        report = self.generate_report()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Report saved to {filename}")
        print(report)
    
    def save_json_results(self, filename: str = "rag_comparison_results.json") -> None:
        """Save detailed results as JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"JSON results saved to {filename}")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run RAG comparison tests"""
    
    logger.info("\n" + "="*80)
    logger.info("STARTING RAG COMPARISON TESTS")
    logger.info("="*80)
    
    comparator = RAGComparator()
    
    # Test without RAG
    logger.info("\nTesting LLM-Only (no retrieval)...")
    comparator.test_mode("without_rag", TEST_QUERIES)
    
    # Test with RAG
    logger.info("\nTesting RAG-Enhanced (with retrieval)...")
    comparator.test_mode("with_rag", TEST_QUERIES)
    
    # Generate and save reports
    logger.info("\n" + "="*80)
    logger.info("GENERATING REPORTS")
    logger.info("="*80)
    
    comparator.save_report("rag_comparison_report.txt")
    comparator.save_json_results("rag_comparison_results.json")
    
    logger.info("\n✓ Comparison complete!")
    logger.info("Reports saved to:")
    logger.info("  - rag_comparison_report.txt (human-readable)")
    logger.info("  - rag_comparison_results.json (machine-readable)")


if __name__ == "__main__":
    main()
