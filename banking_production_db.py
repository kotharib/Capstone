"""
Production Banking Database Schema
Real-world banking tables for support agent
"""

import sqlite3
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Schema Definition
# ============================================================================

SCHEMA = """
-- Customers (Banking Customers)
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    date_of_birth DATE,
    ssn_last_4 TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    kyc_verified BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts (Customer Bank Accounts)
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    account_type TEXT NOT NULL,
    account_number TEXT UNIQUE NOT NULL,
    balance REAL DEFAULT 0.0,
    available_balance REAL DEFAULT 0.0,
    overdraft_limit REAL DEFAULT 0.0,
    interest_rate REAL DEFAULT 0.0,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Transactions (Account Activity)
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'completed',
    merchant_name TEXT,
    merchant_category TEXT,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    posted_date TIMESTAMP,
    reference_number TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Products (Banking Products Catalog)
CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    product_type TEXT NOT NULL,
    description TEXT,
    interest_rate REAL,
    minimum_balance REAL,
    monthly_fee REAL,
    features TEXT,
    status TEXT DEFAULT 'active'
);

-- Support Tickets (Customer Support)
CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    priority TEXT DEFAULT 'normal',
    status TEXT DEFAULT 'open',
    assigned_to TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Cards (Credit/Debit Cards)
CREATE TABLE IF NOT EXISTS cards (
    card_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    card_type TEXT NOT NULL,
    card_number TEXT NOT NULL,
    cardholder_name TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    cvv_last_3 TEXT,
    status TEXT DEFAULT 'active',
    daily_limit REAL DEFAULT 1000.0,
    spending_today REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Fraud Reports (Fraud Alerts)
CREATE TABLE IF NOT EXISTS fraud_reports (
    report_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    transaction_id TEXT,
    report_type TEXT NOT NULL,
    severity TEXT DEFAULT 'low',
    status TEXT DEFAULT 'under_review',
    description TEXT,
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
);

-- Loans (Customer Loans)
CREATE TABLE IF NOT EXISTS loans (
    loan_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    loan_type TEXT NOT NULL,
    principal_amount REAL NOT NULL,
    interest_rate REAL NOT NULL,
    loan_term_months INTEGER,
    monthly_payment REAL,
    balance REAL NOT NULL,
    status TEXT DEFAULT 'active',
    origination_date DATE,
    maturity_date DATE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Audit Log (Compliance & Security)
CREATE TABLE IF NOT EXISTS audit_log (
    log_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    action TEXT NOT NULL,
    user_id TEXT,
    details TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent Activity Log (Tool Usage Tracking)
CREATE TABLE IF NOT EXISTS agent_activity_log (
    activity_id TEXT PRIMARY KEY,
    tool_name TEXT NOT NULL,
    tool_params TEXT,
    success BOOLEAN,
    result TEXT,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    query_context TEXT
);
"""

# ============================================================================
# Production Data Initialization
# ============================================================================

def create_production_database(db_path: str = "banking_production.db") -> bool:
    """Create production banking database with schema and sample data"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create schema
        for statement in SCHEMA.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        conn.commit()
        logger.info(f"✓ Schema created: {db_path}")
        
        # Load sample data
        if _load_sample_data(conn):
            logger.info("✓ Sample data loaded")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ Database creation failed: {e}")
        return False


def _load_sample_data(conn: sqlite3.Connection) -> bool:
    """Load realistic sample data"""
    try:
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM customers")
        if cursor.fetchone()[0] > 0:
            return True  # Data already loaded
        
        # Insert sample customers
        customers = [
            ('CUST001', 'John', 'Smith', 'john.smith@email.com', '555-0101', '1985-05-15', '1234', '123 Main St', 'New York', 'NY', '10001'),
            ('CUST002', 'Jane', 'Doe', 'jane.doe@email.com', '555-0102', '1990-08-22', '5678', '456 Oak Ave', 'Los Angeles', 'CA', '90001'),
            ('CUST003', 'Michael', 'Johnson', 'michael.j@email.com', '555-0103', '1988-03-10', '9012', '789 Pine Rd', 'Chicago', 'IL', '60601'),
            ('CUST004', 'Sarah', 'Williams', 'sarah.w@email.com', '555-0104', '1992-11-28', '3456', '321 Elm St', 'Houston', 'TX', '77001'),
            ('CUST005', 'Robert', 'Brown', 'robert.b@email.com', '555-0105', '1980-07-05', '7890', '654 Maple Dr', 'Phoenix', 'AZ', '85001'),
        ]
        
        cursor.executemany("""
            INSERT INTO customers (customer_id, first_name, last_name, email, phone, 
                                  date_of_birth, ssn_last_4, address, city, state, zip_code, kyc_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, customers)
        
        # Insert sample accounts
        accounts = [
            ('ACC001', 'CUST001', 'Checking', '1234567890', 5250.50, 5000.00, 500.0, 0.01),
            ('ACC002', 'CUST001', 'Savings', '1234567891', 25000.00, 25000.00, 0.0, 0.045),
            ('ACC003', 'CUST002', 'Checking', '1234567892', 3150.25, 3000.00, 500.0, 0.01),
            ('ACC004', 'CUST002', 'Money Market', '1234567893', 50000.00, 50000.00, 0.0, 0.038),
            ('ACC005', 'CUST003', 'Checking', '1234567894', 1500.75, 1500.00, 1000.0, 0.01),
            ('ACC006', 'CUST004', 'Savings', '1234567895', 15000.00, 15000.00, 0.0, 0.045),
            ('ACC007', 'CUST005', 'Checking', '1234567896', 8500.00, 8000.00, 500.0, 0.01),
        ]
        
        cursor.executemany("""
            INSERT INTO accounts (account_id, customer_id, account_type, account_number, 
                                 balance, available_balance, overdraft_limit, interest_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, accounts)
        
        # Insert sample transactions
        now = datetime.now()
        transactions = [
            ('TXN001', 'ACC001', 'debit', 50.00, 'Grocery Store', 'completed', 'Walmart', 'Retail', now - timedelta(days=1)),
            ('TXN002', 'ACC001', 'debit', 25.50, 'Gas Station', 'completed', 'Shell', 'Gas', now - timedelta(days=1)),
            ('TXN003', 'ACC001', 'credit', 2500.00, 'Salary Deposit', 'completed', 'Employer', 'Income', now - timedelta(days=2)),
            ('TXN004', 'ACC002', 'debit', 100.00, 'ATM Withdrawal', 'completed', 'ATM', 'Cash', now - timedelta(hours=6)),
            ('TXN005', 'ACC003', 'debit', 15.99, 'Online Shopping', 'completed', 'Amazon', 'Retail', now - timedelta(hours=12)),
            ('TXN006', 'ACC003', 'debit', 200.00, 'Utility Payment', 'completed', 'Electric Co', 'Utilities', now - timedelta(days=3)),
            ('TXN007', 'ACC001', 'debit', 3500.00, 'Suspicious Activity', 'flagged', 'Unknown', 'Unknown', now - timedelta(hours=2)),
        ]
        
        for txn in transactions:
            cursor.execute("""
                INSERT INTO transactions (transaction_id, account_id, transaction_type, 
                                         amount, description, status, merchant_name, 
                                         merchant_category, transaction_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, txn)
        
        # Insert sample products
        products = [
            ('PROD001', 'Basic Checking', 'checking', 'Free checking account', 0.01, 0, 0, 'Free ATM access, Online banking'),
            ('PROD002', 'Premium Checking', 'checking', 'Premium checking with benefits', 0.015, 1000, 0, 'Premium ATM access, Priority support'),
            ('PROD003', 'Savings Account', 'savings', 'High-yield savings', 0.045, 100, 0, 'Compound daily interest'),
            ('PROD004', 'Money Market', 'savings', 'Money market account', 0.038, 10000, 0, 'Check writing, Higher interest'),
            ('PROD005', 'Personal Loan', 'loan', 'Unsecured personal loan', 0.065, 0, 0, 'Quick approval, Flexible terms'),
            ('PROD006', 'Debit Card', 'card', 'Visa Debit Card', 0, 0, 0, 'Fraud protection, Global acceptance'),
        ]
        
        cursor.executemany("""
            INSERT INTO products (product_id, product_name, product_type, description, 
                                 interest_rate, minimum_balance, monthly_fee, features)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, products)
        
        # Insert sample cards
        cards = [
            ('CARD001', 'ACC001', 'debit', '1234567890123456', 'John Smith', '06/25', '123'),
            ('CARD002', 'ACC002', 'debit', '1234567890123457', 'John Smith', '09/26', '456'),
            ('CARD003', 'ACC003', 'debit', '1234567890123458', 'Jane Doe', '12/24', '789'),
            ('CARD004', 'ACC005', 'debit', '1234567890123459', 'Michael Johnson', '03/25', '012'),
        ]
        
        cursor.executemany("""
            INSERT INTO cards (card_id, account_id, card_type, card_number, 
                              cardholder_name, expiry_date, cvv_last_3)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, cards)
        
        # Insert sample support tickets
        tickets = [
            ('TICK001', 'CUST001', 'Card Lost', 'My debit card is missing', 'card', 'high', 'open'),
            ('TICK002', 'CUST002', 'Unauthorized Transaction', 'Found unknown charges', 'fraud', 'high', 'open'),
            ('TICK003', 'CUST003', 'Account Access Issue', 'Cannot login to online banking', 'technical', 'normal', 'open'),
            ('TICK004', 'CUST004', 'Interest Rate Question', 'Question about savings rate', 'product', 'normal', 'resolved'),
        ]
        
        for ticket in tickets:
            cursor.execute("""
                INSERT INTO support_tickets (ticket_id, customer_id, subject, 
                                            description, category, priority, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ticket)
        
        # Insert sample loans
        loans = [
            ('LOAN001', 'CUST001', 'Personal Loan', 50000.00, 0.065, 60, 943.56, 42000.00),
            ('LOAN002', 'CUST004', 'Home Equity Loan', 150000.00, 0.055, 120, 1580.50, 135000.00),
        ]
        
        cursor.executemany("""
            INSERT INTO loans (loan_id, customer_id, loan_type, principal_amount, 
                              interest_rate, loan_term_months, monthly_payment, balance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, loans)
        
        # Insert sample fraud reports
        fraud = [
            ('FRAUD001', 'ACC001', 'TXN007', 'suspicious_transaction', 'high', 'under_review', 'Unusual large transaction detected'),
        ]
        
        cursor.executemany("""
            INSERT INTO fraud_reports (report_id, account_id, transaction_id, 
                                      report_type, severity, status, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, fraud)
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"✗ Error loading sample data: {e}")
        return False


class ProductionDatabase:
    """Production banking database interface"""
    
    def __init__(self, db_path: str = "banking_production.db"):
        self.db_path = db_path
    
    def get_customer(self, customer_id: str) -> dict:
        """Get customer details"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_accounts(self, customer_id: str) -> list:
        """Get all accounts for customer"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM accounts WHERE customer_id = ?", (customer_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_account_balance(self, account_id: str) -> dict:
        """Get account balance"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT account_id, account_number, account_type, balance, 
                   available_balance, status FROM accounts WHERE account_id = ?
        """, (account_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_transactions(self, account_id: str, limit: int = 10) -> list:
        """Get recent transactions"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT transaction_id, account_id, transaction_type, amount, 
                   description, status, merchant_name, transaction_date
            FROM transactions WHERE account_id = ?
            ORDER BY transaction_date DESC LIMIT ?
        """, (account_id, limit))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_fraud_alerts(self, account_id: str) -> list:
        """Get fraud alerts for account"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT report_id, account_id, report_type, severity, status, description
            FROM fraud_reports WHERE account_id = ? AND status IN ('under_review', 'open')
            ORDER BY reported_at DESC
        """, (account_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_support_tickets(self, customer_id: str) -> list:
        """Get support tickets for customer"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ticket_id, subject, category, priority, status, created_at
            FROM support_tickets WHERE customer_id = ?
            ORDER BY created_at DESC
        """, (customer_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_product_info(self, product_id: str) -> dict:
        """Get product details"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def log_activity(self, tool_name: str, params: dict, success: bool, 
                    result: str = None, error: str = None, context: str = None):
        """Log tool usage for audit"""
        import json
        from uuid import uuid4
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO agent_activity_log 
            (activity_id, tool_name, tool_params, success, result, error_message, query_context)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid4()),
            tool_name,
            json.dumps(params),
            success,
            result,
            error,
            context
        ))
        
        conn.commit()
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if create_production_database():
        print("✓ Production database created successfully")
        db = ProductionDatabase()
        customer = db.get_customer("CUST001")
        print(f"\nSample customer: {customer['first_name']} {customer['last_name']}")
    else:
        print("✗ Failed to create production database")
