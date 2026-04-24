"""
Database Initialization
Initialize SQLite database with banking documents from JSON test data
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Initialize and manage SQLite database for banking documents"""
    
    def __init__(self, db_path: str = "banking_docs.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
    
    def create_schema(self):
        """Create database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Metadata table for tracking document updates
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_metadata (
                doc_id TEXT PRIMARY KEY,
                version INTEGER DEFAULT 1,
                source TEXT,
                embedded BOOLEAN DEFAULT 0,
                chunk_count INTEGER DEFAULT 0,
                last_embedded TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES documents(id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database schema created: {self.db_path}")
    
    def load_test_data(self, json_path: str = "banking_documents.json") -> bool:
        """
        Load test data from JSON file into database
        
        Args:
            json_path: Path to JSON test data file
        
        Returns:
            True if successful, False otherwise
        """
        if not Path(json_path).exists():
            logger.error(f"Test data file not found: {json_path}")
            return False
        
        try:
            # Load JSON data
            with open(json_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear existing data
            cursor.execute("DELETE FROM document_metadata")
            cursor.execute("DELETE FROM documents")
            
            # Insert documents
            for doc in documents:
                cursor.execute("""
                    INSERT INTO documents (id, title, category, content)
                    VALUES (?, ?, ?, ?)
                """, (
                    doc['id'],
                    doc['title'],
                    doc['category'],
                    doc['content']
                ))
                
                # Create metadata entry
                cursor.execute("""
                    INSERT INTO document_metadata (doc_id, version, source)
                    VALUES (?, ?, ?)
                """, (doc['id'], 1, 'test_data'))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Loaded {len(documents)} documents from {json_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load test data: {e}")
            return False
    
    def get_all_documents(self) -> List[Dict]:
        """
        Retrieve all documents from database
        
        Returns:
            List of document dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, title, category, content FROM documents ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_document_by_id(self, doc_id: str) -> Dict:
        """
        Retrieve single document by ID
        
        Args:
            doc_id: Document ID
        
        Returns:
            Document dictionary or None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, title, category, content FROM documents WHERE id = ?",
            (doc_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_documents_by_category(self, category: str) -> List[Dict]:
        """
        Retrieve documents by category
        
        Args:
            category: Document category
        
        Returns:
            List of document dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, title, category, content FROM documents WHERE category = ? ORDER BY id",
            (category,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_embedding_status(self, doc_id: str, chunk_count: int):
        """
        Update document embedding status
        
        Args:
            doc_id: Document ID
            chunk_count: Number of chunks created
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE document_metadata
            SET embedded = 1, chunk_count = ?, last_embedded = CURRENT_TIMESTAMP
            WHERE doc_id = ?
        """, (chunk_count, doc_id))
        
        conn.commit()
        conn.close()
    
    def get_document_count(self) -> int:
        """Get total number of documents"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]
        conn.close()
        
        return count


def initialize_database(db_path: str = "banking_docs.db", 
                       test_data_path: str = "banking_documents.json") -> bool:
    """
    Complete database initialization
    
    Args:
        db_path: Path to SQLite database
        test_data_path: Path to JSON test data
    
    Returns:
        True if successful
    """
    initializer = DatabaseInitializer(db_path)
    
    # Create schema
    initializer.create_schema()
    
    # Load test data
    if not initializer.load_test_data(test_data_path):
        return False
    
    # Verify
    count = initializer.get_document_count()
    logger.info(f"Database initialized with {count} documents")
    
    return True


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize database
    if initialize_database():
        print("✓ Database initialization successful")
    else:
        print("✗ Database initialization failed")
