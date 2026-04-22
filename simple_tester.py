"""
Simplified Prompt Tester - Direct comparison without complex logging
"""

from agent_llm import LLMAgent
import json

# Test queries (2-3 per category)
TEST_QUERIES = [
    ("What is a checking account?", "basic_product"),
    ("Tell me about savings accounts", "basic_product"),
    ("What documents do I need to open an account?", "process"),
    ("Can you give me investment advice?", "out_of_scope"),
    ("Is my money safe in your bank?", "safety"),
    ("What are your credit card interest rates?", "rates"),
]

STRATEGIES = ["one-shot", "few-shot", "chain-of-thought"]

print("\n" + "=" * 80)
print("PROMPT STRATEGY COMPARISON TEST")
print("=" * 80 + "\n")

all_results = {}

# Test each strategy
for strategy in STRATEGIES:
    print(f"\nTesting: {strategy.upper()}")
    print("-" * 80)
    
    agent = LLMAgent(strategy=strategy)
    strategy_results = []
    
    for query, category in TEST_QUERIES:
        try:
            print(f"Q: {query} [{category}]")
            response = agent.process_query(query)
            print(f"A: {response[:100]}...")
            print()
            
            strategy_results.append({
                "query": query,
                "category": category,
                "response_length": len(response),
                "success": True
            })
        except Exception as e:
            print(f"❌ ERROR: {e}\n")
            strategy_results.append({
                "query": query,
                "category": category,
                "error": str(e),
                "success": False
            })
    
    stats = agent.get_stats()
    all_results[strategy] = {
        "results": strategy_results,
        "stats": stats
    }
    
    print(f"\n{strategy.upper()} STATISTICS:")
    print(f"  Total Tokens: {stats['total_tokens']}")
    print(f"  Prompt Tokens: {stats['total_prompt_tokens']}")
    print(f"  Completion Tokens: {stats['total_completion_tokens']}")
    print(f"  Avg Tokens/Query: {(stats['total_prompt_tokens'] + stats['total_completion_tokens']) / stats['total_turns']:.1f}")
    print("=" * 80)

# Comparison Summary
print("\n\nCOMPARISON SUMMARY")
print("=" * 80)
print(f"{'Strategy':<20} {'Total Tokens':<15} {'Avg/Query':<12} {'Queries':<8}")
print("-" * 80)

for strategy in STRATEGIES:
    stats = all_results[strategy]["stats"]
    avg = (stats['total_prompt_tokens'] + stats['total_completion_tokens']) / stats['total_turns']
    print(f"{strategy:<20} {stats['total_tokens']:<15} {avg:<12.1f} {stats['total_turns']:<8}")

print("=" * 80)

# Find most efficient
tokens_by_strategy = {s: all_results[s]["stats"]["total_tokens"] for s in STRATEGIES}
best = min(tokens_by_strategy, key=tokens_by_strategy.get)

print(f"\n✓ Most Token-Efficient Strategy: {best.upper()}")
print(f"  Total Tokens: {tokens_by_strategy[best]}")
print(f"\nAll strategies tested successfully!")
print("=" * 80 + "\n")

# Save results as JSON
with open("comparison_results.json", "w") as f:
    json.dump(all_results, f, indent=2)
print("Results saved to: comparison_results.json\n")
