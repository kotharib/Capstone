"""
Banking Support Agent with Tool Calling
Demonstrates correct/incorrect tool usage with safeguards
"""

import logging
import json
from typing import List, Dict, Tuple, Any
from agent_tools import BankingSupportTools
from banking_production_db import ProductionDatabase

logger = logging.getLogger(__name__)

# ============================================================================
# Tool Routing & Selection Logic
# ============================================================================

class SupportAgentRouter:
    """Routes customer queries to appropriate tools"""
    
    def __init__(self):
        self.query_keywords = {
            "lookup_customer": ["who", "customer", "profile", "information"],
            "check_account_balance": ["balance", "account", "how much", "money"],
            "get_transaction_history": ["transaction", "history", "activity", "charges", "payments"],
            "check_fraud_alerts": ["fraud", "suspicious", "unauthorized", "alert", "theft"],
            "get_support_tickets": ["ticket", "issue", "problem", "support", "complaint"],
            "get_product_info": ["product", "account type", "savings", "checking", "loan"]
        }
    
    def route_query(self, query: str) -> List[Tuple[str, float]]:
        """
        Route query to tools with confidence scores
        
        Returns:
            List of (tool_name, confidence) tuples sorted by confidence
        """
        query_lower = query.lower()
        scores = {}
        
        for tool_name, keywords in self.query_keywords.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            score = matches / len(keywords)
            scores[tool_name] = score
        
        # Filter and sort by confidence
        routes = [(tool, score) for tool, score in scores.items() if score > 0]
        routes.sort(key=lambda x: x[1], reverse=True)
        
        return routes


# ============================================================================
# Support Agent
# ============================================================================

class BankingSupportAgent:
    """Support agent with tool calling and safeguards"""
    
    def __init__(self):
        """Initialize agent"""
        self.db = ProductionDatabase()
        self.tools = BankingSupportTools(self.db)
        self.router = SupportAgentRouter()
        self.conversation_history: List[Dict] = []
        self.call_count = 0
    
    def process_query(self, user_query: str, customer_id: str = None, 
                     account_id: str = None) -> Dict[str, Any]:
        """
        Process customer query and return response with tool calls
        
        Args:
            user_query: Customer's question
            customer_id: Customer ID (optional, for context)
            account_id: Account ID (optional, for context)
        
        Returns:
            Response dictionary with tool calls and results
        """
        self.call_count += 1
        response = {
            "query": user_query,
            "call_number": self.call_count,
            "tool_calls": [],
            "responses": [],
            "summary": "",
            "success": True
        }
        
        logger.info(f"\n{'='*70}")
        logger.info(f"CALL #{self.call_count}: Processing query")
        logger.info(f"Query: {user_query}")
        if customer_id:
            logger.info(f"Customer: {customer_id}")
        logger.info(f"{'='*70}")
        
        # Step 1: Route query to tools
        routes = self.router.route_query(user_query)
        
        if not routes:
            response["summary"] = "I couldn't understand your query. Please provide more details."
            response["success"] = False
            return response
        
        logger.info(f"\nRouting analysis:")
        for tool_name, confidence in routes[:3]:
            logger.info(f"  - {tool_name}: {confidence:.0%} confidence")
        
        # Step 2: Try top tools with context
        best_tool = routes[0][0]
        tool_params = self._build_tool_params(best_tool, customer_id, account_id)
        
        logger.info(f"\nSelected tool: {best_tool}")
        logger.info(f"Parameters: {json.dumps(tool_params, indent=2)}")
        
        # Step 3: Execute tool
        logger.info(f"\nExecuting tool...")
        result = self.tools.execute_tool(best_tool, tool_params, context=user_query)
        
        response["tool_calls"].append({
            "tool": best_tool,
            "params": tool_params,
            "status": result["status"]
        })
        
        response["responses"].append(result)
        
        # Step 4: Generate response
        if result["status"] == "success":
            response["summary"] = self._format_response(best_tool, result["result"])
        else:
            response["summary"] = f"Error: {result['error']}"
            response["success"] = False
        
        # Log to conversation history
        self.conversation_history.append(response)
        
        return response
    
    def _build_tool_params(self, tool_name: str, customer_id: str = None,
                          account_id: str = None) -> Dict:
        """Build parameters for tool call based on context"""
        params = {}
        
        tool = self.tools.tools[tool_name]
        
        for param in tool.required_params:
            if param == "customer_id":
                params[param] = customer_id or "CUST001"
            elif param == "account_id":
                params[param] = account_id or "ACC001"
            elif param == "product_id":
                params[param] = "PROD001"
            elif param == "limit":
                params[param] = 10
        
        return params
    
    def _format_response(self, tool_name: str, result: Dict) -> str:
        """Format tool result into human-readable response"""
        if tool_name == "lookup_customer":
            return f"Customer: {result['name']} ({result['customer_id']}). KYC Status: {'Verified' if result['kyc_verified'] else 'Pending'}"
        
        elif tool_name == "check_account_balance":
            return f"Account {result['account_id']} ({result['account_type']}): Balance: ${result['balance']:.2f}, Available: ${result['available_balance']:.2f}"
        
        elif tool_name == "get_transaction_history":
            if result['transaction_count'] == 0:
                return "No transactions found."
            return f"Found {result['transaction_count']} transactions. Recent: {result['transactions'][0]['description']} for ${result['transactions'][0]['amount']:.2f}"
        
        elif tool_name == "check_fraud_alerts":
            if result['alert_count'] == 0:
                return "No fraud alerts on this account. Account is secure."
            return f"⚠️  {result['alert_count']} fraud alert(s) found. Severity: {result['severity']}. Please review immediately."
        
        elif tool_name == "get_support_tickets":
            if result['ticket_count'] == 0:
                return "No active support tickets."
            return f"Found {result['ticket_count']} active ticket(s). Most recent: {result['tickets'][0]['subject']}"
        
        elif tool_name == "get_product_info":
            return f"{result['product_name']}: {result['description']}. Interest Rate: {result['interest_rate']:.2%}, Monthly Fee: ${result['monthly_fee']}"
        
        return "Success"
    
    def demonstrate_incorrect_tool_usage(self) -> List[Dict]:
        """Demonstrate common incorrect tool usage patterns"""
        logger.info("\n" + "="*70)
        logger.info("DEMONSTRATING INCORRECT TOOL USAGE PATTERNS")
        logger.info("="*70)
        
        mistakes = []
        
        # Mistake 1: Missing required parameter
        logger.info("\n[MISTAKE 1] Missing Required Parameter")
        logger.info("-" * 70)
        result = self.tools.execute_tool("check_account_balance", 
                                        {"account_id": "ACC001"},  # Missing customer_id
                                        context="Incorrect: missing customer_id")
        logger.info(f"Result: {result['status']}")
        logger.info(f"Error: {result['error']}")
        mistakes.append({"type": "missing_parameter", "result": result})
        
        # Mistake 2: Invalid parameter type
        logger.info("\n[MISTAKE 2] Invalid Parameter Type")
        logger.info("-" * 70)
        result = self.tools.execute_tool("get_transaction_history",
                                        {"account_id": "ACC001", "customer_id": "CUST001", "limit": "10"},  # Should be int
                                        context="Incorrect: limit is string not integer")
        logger.info(f"Result: {result['status']}")
        logger.info(f"Error: {result['error']}")
        mistakes.append({"type": "invalid_type", "result": result})
        
        # Mistake 3: Invalid parameter value
        logger.info("\n[MISTAKE 3] Invalid Parameter Value")
        logger.info("-" * 70)
        result = self.tools.execute_tool("get_transaction_history",
                                        {"account_id": "ACC001", "customer_id": "CUST001", "limit": 100},  # Exceeds max
                                        context="Incorrect: limit exceeds maximum")
        logger.info(f"Result: {result['status']}")
        logger.info(f"Error: {result['error']}")
        mistakes.append({"type": "invalid_value", "result": result})
        
        # Mistake 4: Non-existent tool
        logger.info("\n[MISTAKE 4] Non-Existent Tool")
        logger.info("-" * 70)
        result = self.tools.execute_tool("transfer_funds", 
                                        {"amount": 1000},  # Tool doesn't exist
                                        context="Incorrect: tool doesn't exist")
        logger.info(f"Result: {result['status']}")
        logger.info(f"Error: {result['error']}")
        mistakes.append({"type": "non_existent_tool", "result": result})
        
        # Mistake 5: Access violation
        logger.info("\n[MISTAKE 5] Access Violation")
        logger.info("-" * 70)
        result = self.tools.execute_tool("check_account_balance",
                                        {"account_id": "ACC001", "customer_id": "CUST999"},  # Wrong customer
                                        context="Incorrect: customer doesn't own account")
        logger.info(f"Result: {result['status']}")
        logger.info(f"Error: {result['error']}")
        mistakes.append({"type": "access_violation", "result": result})
        
        # Mistake 6: Loop detection
        logger.info("\n[MISTAKE 6] Loop Detection (repeated calls)")
        logger.info("-" * 70)
        params = {"customer_id": "CUST001"}
        for i in range(4):
            logger.info(f"  Call {i+1}...")
            result = self.tools.execute_tool("get_product_info",
                                            params,
                                            context="Loop test")
            logger.info(f"    Status: {result['status']}")
            if result['status'] == 'failure':
                logger.info(f"    Error: {result['error']}")
                mistakes.append({"type": "loop_detection", "result": result})
                break
        
        return mistakes
    
    def demonstrate_correct_tool_usage(self) -> List[Dict]:
        """Demonstrate correct tool usage patterns"""
        logger.info("\n" + "="*70)
        logger.info("DEMONSTRATING CORRECT TOOL USAGE PATTERNS")
        logger.info("="*70)
        
        successful_calls = []
        
        # Correct 1: Lookup customer
        logger.info("\n[CORRECT 1] Lookup Customer")
        logger.info("-" * 70)
        result = self.process_query("Who is customer CUST001?", customer_id="CUST001")
        logger.info(f"Response: {result['summary']}")
        successful_calls.append(result)
        
        # Correct 2: Check account balance
        logger.info("\n[CORRECT 2] Check Account Balance")
        logger.info("-" * 70)
        result = self.process_query("What is my account balance?", 
                                   customer_id="CUST001", account_id="ACC001")
        logger.info(f"Response: {result['summary']}")
        successful_calls.append(result)
        
        # Correct 3: Get transaction history
        logger.info("\n[CORRECT 3] Get Transaction History")
        logger.info("-" * 70)
        result = self.process_query("Show me my recent transactions",
                                   customer_id="CUST002", account_id="ACC003")
        logger.info(f"Response: {result['summary']}")
        successful_calls.append(result)
        
        # Correct 4: Check fraud alerts
        logger.info("\n[CORRECT 4] Check Fraud Alerts")
        logger.info("-" * 70)
        result = self.process_query("Are there any fraud alerts on my account?",
                                   customer_id="CUST001", account_id="ACC001")
        logger.info(f"Response: {result['summary']}")
        successful_calls.append(result)
        
        # Correct 5: Get support tickets
        logger.info("\n[CORRECT 5] Get Support Tickets")
        logger.info("-" * 70)
        result = self.process_query("What support tickets do I have?",
                                   customer_id="CUST001")
        logger.info(f"Response: {result['summary']}")
        successful_calls.append(result)
        
        # Correct 6: Get product info
        logger.info("\n[CORRECT 6] Get Product Information")
        logger.info("-" * 70)
        result = self.tools.execute_tool("get_product_info",
                                        {"product_id": "PROD003"},
                                        context="Product inquiry")
        logger.info(f"Status: {result['status']}")
        if result['status'] == 'success':
            logger.info(f"Product: {result['result']['product_name']}")
            logger.info(f"Interest Rate: {result['result']['interest_rate']:.2%}")
        successful_calls.append(result)
        
        return successful_calls


# ============================================================================
# Demonstration & Testing
# ============================================================================

def main():
    """Run complete demonstration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    logger.info("\n" + "="*70)
    logger.info("BANKING SUPPORT AGENT - TOOL CALLING DEMONSTRATION")
    logger.info("="*70)
    
    agent = BankingSupportAgent()
    
    # Show available tools
    logger.info("\nAvailable Tools:")
    tools_info = agent.tools.get_tool_schema()
    for i, (tool_name, info) in enumerate(tools_info.items(), 1):
        logger.info(f"{i}. {tool_name}")
        logger.info(f"   {info['description']}")
    
    # Demonstrate correct usage
    correct_calls = agent.demonstrate_correct_tool_usage()
    
    # Demonstrate incorrect usage
    incorrect_calls = agent.demonstrate_incorrect_tool_usage()
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("SUMMARY")
    logger.info("="*70)
    logger.info(f"Total tool calls: {agent.tools.session_calls.__len__()}")
    logger.info(f"Successful calls: {len([c for c in correct_calls if c.get('success', True)])}")
    logger.info(f"Failed calls detected: {len(incorrect_calls)}")
    logger.info(f"\nSafeguards Demonstrated:")
    logger.info(f"  ✓ Parameter validation")
    logger.info(f"  ✓ Access control (customer verification)")
    logger.info(f"  ✓ Loop detection")
    logger.info(f"  ✓ Rate limiting")
    logger.info(f"  ✓ Error handling")
    logger.info(f"  ✓ Audit logging")
    
    logger.info("\n" + "="*70)
    logger.info("DEMONSTRATION COMPLETE")
    logger.info("="*70)


if __name__ == "__main__":
    main()
