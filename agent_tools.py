"""
Banking Support Agent: Tool System
Tool definitions, routing, and execution with safeguards
"""

import logging
import json
from typing import Dict, List, Callable, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import hashlib
from datetime import datetime, timedelta

from banking_production_db import ProductionDatabase

logger = logging.getLogger(__name__)

# ============================================================================
# Tool Definitions & Schemas
# ============================================================================

class ToolResult(Enum):
    """Tool execution result status"""
    SUCCESS = "success"
    FAILURE = "failure"
    PERMISSION_DENIED = "permission_denied"
    INVALID_PARAMS = "invalid_params"
    RATE_LIMITED = "rate_limited"


@dataclass
class Tool:
    """Tool definition with schema and metadata"""
    name: str
    description: str
    parameters: Dict[str, Any]
    required_params: List[str]
    callable: Callable
    requires_auth: bool = False
    rate_limit: int = 10  # max calls per hour
    read_only: bool = False


# ============================================================================
# Tool Library
# ============================================================================

class BankingSupportTools:
    """Banking support agent tools with validation and safeguards"""
    
    def __init__(self, db: ProductionDatabase = None):
        """Initialize tools with database"""
        self.db = db or ProductionDatabase()
        self.call_history: Dict[str, list] = {}  # Track calls for rate limiting
        self.session_calls: List[Dict] = []  # Track calls in session
        
        # Define available tools
        self.tools: Dict[str, Tool] = {
            "lookup_customer": Tool(
                name="lookup_customer",
                description="Look up customer information by ID",
                parameters={
                    "customer_id": {"type": "string", "description": "Customer ID (e.g., CUST001)"}
                },
                required_params=["customer_id"],
                callable=self._lookup_customer,
                requires_auth=True,
                rate_limit=20
            ),
            
            "check_account_balance": Tool(
                name="check_account_balance",
                description="Check account balance and availability",
                parameters={
                    "account_id": {"type": "string", "description": "Account ID (e.g., ACC001)"},
                    "customer_id": {"type": "string", "description": "Customer ID for verification"}
                },
                required_params=["account_id", "customer_id"],
                callable=self._check_account_balance,
                requires_auth=True,
                rate_limit=30,
                read_only=True
            ),
            
            "get_transaction_history": Tool(
                name="get_transaction_history",
                description="Retrieve recent transactions for an account",
                parameters={
                    "account_id": {"type": "string", "description": "Account ID"},
                    "customer_id": {"type": "string", "description": "Customer ID for verification"},
                    "limit": {"type": "integer", "description": "Number of transactions (max 50)", "default": 10}
                },
                required_params=["account_id", "customer_id"],
                callable=self._get_transaction_history,
                requires_auth=True,
                rate_limit=20,
                read_only=True
            ),
            
            "check_fraud_alerts": Tool(
                name="check_fraud_alerts",
                description="Check for active fraud alerts on an account",
                parameters={
                    "account_id": {"type": "string", "description": "Account ID"},
                    "customer_id": {"type": "string", "description": "Customer ID for verification"}
                },
                required_params=["account_id", "customer_id"],
                callable=self._check_fraud_alerts,
                requires_auth=True,
                rate_limit=15,
                read_only=True
            ),
            
            "get_support_tickets": Tool(
                name="get_support_tickets",
                description="Retrieve support tickets for a customer",
                parameters={
                    "customer_id": {"type": "string", "description": "Customer ID"},
                    "include_resolved": {"type": "boolean", "description": "Include resolved tickets", "default": False}
                },
                required_params=["customer_id"],
                callable=self._get_support_tickets,
                requires_auth=True,
                rate_limit=20,
                read_only=True
            ),
            
            "get_product_info": Tool(
                name="get_product_info",
                description="Get information about banking products",
                parameters={
                    "product_id": {"type": "string", "description": "Product ID (e.g., PROD001)"}
                },
                required_params=["product_id"],
                callable=self._get_product_info,
                requires_auth=False,
                rate_limit=50,
                read_only=True
            )
        }
    
    # ========================================================================
    # Tool Implementations
    # ========================================================================
    
    def _lookup_customer(self, customer_id: str) -> Tuple[bool, Dict]:
        """Look up customer information"""
        try:
            # Validate customer_id format
            if not customer_id.startswith("CUST"):
                return False, {"error": "Invalid customer ID format"}
            
            customer = self.db.get_customer(customer_id)
            if not customer:
                return False, {"error": f"Customer {customer_id} not found"}
            
            # Return sanitized customer info (no sensitive data)
            return True, {
                "customer_id": customer["customer_id"],
                "name": f"{customer['first_name']} {customer['last_name']}",
                "email": customer["email"],
                "kyc_verified": bool(customer["kyc_verified"]),
                "member_since": customer["created_at"]
            }
        except Exception as e:
            return False, {"error": str(e)}
    
    def _check_account_balance(self, account_id: str, customer_id: str) -> Tuple[bool, Dict]:
        """Check account balance"""
        try:
            # Verify customer owns account
            accounts = self.db.get_accounts(customer_id)
            account_ids = [acc["account_id"] for acc in accounts]
            
            if account_id not in account_ids:
                return False, {"error": "Access denied: Account not owned by customer"}
            
            balance = self.db.get_account_balance(account_id)
            if not balance:
                return False, {"error": f"Account {account_id} not found"}
            
            return True, {
                "account_id": balance["account_id"],
                "account_type": balance["account_type"],
                "balance": balance["balance"],
                "available_balance": balance["available_balance"],
                "status": balance["status"]
            }
        except Exception as e:
            return False, {"error": str(e)}
    
    def _get_transaction_history(self, account_id: str, customer_id: str, 
                                 limit: int = 10) -> Tuple[bool, Dict]:
        """Get transaction history"""
        try:
            # Validate limit
            if limit > 50:
                return False, {"error": "Limit cannot exceed 50 transactions"}
            
            # Verify account ownership
            accounts = self.db.get_accounts(customer_id)
            account_ids = [acc["account_id"] for acc in accounts]
            
            if account_id not in account_ids:
                return False, {"error": "Access denied: Account not owned by customer"}
            
            transactions = self.db.get_transactions(account_id, limit)
            
            return True, {
                "account_id": account_id,
                "transaction_count": len(transactions),
                "transactions": transactions
            }
        except Exception as e:
            return False, {"error": str(e)}
    
    def _check_fraud_alerts(self, account_id: str, customer_id: str) -> Tuple[bool, Dict]:
        """Check for fraud alerts"""
        try:
            # Verify account ownership
            accounts = self.db.get_accounts(customer_id)
            account_ids = [acc["account_id"] for acc in accounts]
            
            if account_id not in account_ids:
                return False, {"error": "Access denied: Account not owned by customer"}
            
            alerts = self.db.get_fraud_alerts(account_id)
            
            return True, {
                "account_id": account_id,
                "alert_count": len(alerts),
                "alerts": alerts,
                "severity": max([a["severity"] for a in alerts], default="none")
            }
        except Exception as e:
            return False, {"error": str(e)}
    
    def _get_support_tickets(self, customer_id: str, 
                            include_resolved: bool = False) -> Tuple[bool, Dict]:
        """Get support tickets"""
        try:
            tickets = self.db.get_support_tickets(customer_id)
            
            if not include_resolved:
                tickets = [t for t in tickets if t["status"] != "resolved"]
            
            return True, {
                "customer_id": customer_id,
                "ticket_count": len(tickets),
                "tickets": tickets
            }
        except Exception as e:
            return False, {"error": str(e)}
    
    def _get_product_info(self, product_id: str) -> Tuple[bool, Dict]:
        """Get product information"""
        try:
            # Validate product_id format
            if not product_id.startswith("PROD"):
                return False, {"error": "Invalid product ID format"}
            
            product = self.db.get_product_info(product_id)
            if not product:
                return False, {"error": f"Product {product_id} not found"}
            
            return True, {
                "product_id": product["product_id"],
                "product_name": product["product_name"],
                "product_type": product["product_type"],
                "description": product["description"],
                "interest_rate": product["interest_rate"],
                "minimum_balance": product["minimum_balance"],
                "monthly_fee": product["monthly_fee"],
                "features": product["features"]
            }
        except Exception as e:
            return False, {"error": str(e)}
    
    # ========================================================================
    # Tool Execution & Safeguards
    # ========================================================================
    
    def validate_tool_call(self, tool_name: str, params: Dict) -> Tuple[bool, str]:
        """Validate tool call parameters"""
        if tool_name not in self.tools:
            return False, f"Unknown tool: {tool_name}"
        
        tool = self.tools[tool_name]
        
        # Check required parameters
        for required in tool.required_params:
            if required not in params:
                return False, f"Missing required parameter: {required}"
        
        # Validate parameter types
        for param_name, param_value in params.items():
            if param_name not in tool.parameters:
                return False, f"Unknown parameter: {param_name}"
            
            expected_type = tool.parameters[param_name].get("type")
            if expected_type == "integer" and not isinstance(param_value, int):
                return False, f"Parameter {param_name} must be integer"
            elif expected_type == "string" and not isinstance(param_value, str):
                return False, f"Parameter {param_name} must be string"
            elif expected_type == "boolean" and not isinstance(param_value, bool):
                return False, f"Parameter {param_name} must be boolean"
        
        return True, ""
    
    def check_rate_limit(self, tool_name: str) -> Tuple[bool, str]:
        """Check if tool call exceeds rate limit"""
        if tool_name not in self.tools:
            return False, "Unknown tool"
        
        tool = self.tools[tool_name]
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Initialize history if needed
        if tool_name not in self.call_history:
            self.call_history[tool_name] = []
        
        # Clean old calls
        self.call_history[tool_name] = [
            call_time for call_time in self.call_history[tool_name]
            if call_time > one_hour_ago
        ]
        
        # Check limit
        if len(self.call_history[tool_name]) >= tool.rate_limit:
            return False, f"Rate limit exceeded for {tool_name} ({tool.rate_limit}/hour)"
        
        return True, ""
    
    def detect_loops(self, tool_name: str, params: Dict) -> Tuple[bool, str]:
        """Detect potential infinite loops"""
        # Create a call signature
        call_sig = f"{tool_name}:{json.dumps(params, sort_keys=True)}"
        call_hash = hashlib.md5(call_sig.encode()).hexdigest()
        
        # Check if same call repeated in last 10 calls
        recent_calls = self.session_calls[-10:]
        call_counts = {}
        for call in recent_calls:
            h = call["hash"]
            call_counts[h] = call_counts.get(h, 0) + 1
        
        if call_counts.get(call_hash, 0) >= 3:
            return False, "Loop detected: Same tool call repeated 3+ times"
        
        return True, ""
    
    def execute_tool(self, tool_name: str, params: Dict, 
                    context: str = None) -> Dict[str, Any]:
        """Execute tool with full validation and error handling"""
        
        result = {
            "tool": tool_name,
            "status": "failed",
            "result": None,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
        # Step 1: Validate tool exists
        if tool_name not in self.tools:
            result["error"] = f"Unknown tool: {tool_name}"
            result["status"] = ToolResult.INVALID_PARAMS.value
            self.db.log_activity(tool_name, params, False, error=result["error"], context=context)
            return result
        
        # Step 2: Validate parameters
        valid, error = self.validate_tool_call(tool_name, params)
        if not valid:
            result["error"] = error
            result["status"] = ToolResult.INVALID_PARAMS.value
            self.db.log_activity(tool_name, params, False, error=error, context=context)
            return result
        
        # Step 3: Check rate limits
        limited, error = self.check_rate_limit(tool_name)
        if not limited:
            result["error"] = error
            result["status"] = ToolResult.RATE_LIMITED.value
            self.db.log_activity(tool_name, params, False, error=error, context=context)
            return result
        
        # Step 4: Detect loops
        loop, error = self.detect_loops(tool_name, params)
        if not loop:
            result["error"] = error
            result["status"] = ToolResult.FAILURE.value
            self.db.log_activity(tool_name, params, False, error=error, context=context)
            return result
        
        # Step 5: Execute tool
        try:
            tool = self.tools[tool_name]
            success, output = tool.callable(**params)
            
            if success:
                result["status"] = ToolResult.SUCCESS.value
                result["result"] = output
                self.db.log_activity(tool_name, params, True, 
                                    result=json.dumps(output), context=context)
            else:
                result["status"] = ToolResult.FAILURE.value
                result["error"] = output.get("error", "Unknown error")
                self.db.log_activity(tool_name, params, False, 
                                    error=result["error"], context=context)
        
        except Exception as e:
            result["status"] = ToolResult.FAILURE.value
            result["error"] = str(e)
            self.db.log_activity(tool_name, params, False, error=str(e), context=context)
        
        # Track call for loop detection
        self.session_calls.append({
            "tool": tool_name,
            "hash": hashlib.md5(f"{tool_name}:{json.dumps(params, sort_keys=True)}".encode()).hexdigest(),
            "timestamp": datetime.now()
        })
        
        # Update rate limit history
        if tool_name not in self.call_history:
            self.call_history[tool_name] = []
        self.call_history[tool_name].append(datetime.now())
        
        return result
    
    def get_tool_schema(self, tool_name: str = None) -> Dict:
        """Get tool schema(s) for agent to understand"""
        if tool_name:
            if tool_name not in self.tools:
                return {"error": f"Tool {tool_name} not found"}
            
            tool = self.tools[tool_name]
            return {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "required_params": tool.required_params,
                "read_only": tool.read_only
            }
        else:
            # Return all tools
            return {
                name: {
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "required_params": tool.required_params,
                    "read_only": tool.read_only
                }
                for name, tool in self.tools.items()
            }
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return list(self.tools.keys())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    tools = BankingSupportTools()
    
    print("=" * 60)
    print("BANKING SUPPORT TOOLS SYSTEM")
    print("=" * 60)
    
    print(f"\nAvailable tools: {', '.join(tools.get_available_tools())}")
    
    print("\n" + "=" * 60)
    print("TOOL SCHEMAS")
    print("=" * 60)
    
    schemas = tools.get_tool_schema()
    for tool_name, schema in schemas.items():
        print(f"\n{tool_name}:")
        print(f"  Description: {schema['description']}")
        print(f"  Parameters: {list(schema['parameters'].keys())}")
        print(f"  Required: {schema['required_params']}")
