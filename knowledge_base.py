"""
Banking Knowledge Base
Load documents from SQLite database instead of hardcoded data
"""

import logging
from typing import List, Dict
from pathlib import Path
from db_init import DatabaseInitializer

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """Interface to banking documents stored in SQLite"""
    
    def __init__(self, db_path: str = "banking_docs.db"):
        """
        Initialize knowledge base
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.db_init = DatabaseInitializer(db_path)
        
        # Ensure database exists
        if not Path(db_path).exists():
            logger.info(f"Database not found, initializing: {db_path}")
            from db_init import initialize_database
            initialize_database(db_path)
        
        self._doc_cache = None
        logger.info(f"KnowledgeBase initialized with: {db_path}")
    
    def get_all_documents(self) -> List[Dict]:
        """
        Get all documents from database
        
        Returns:
            List of document dictionaries with keys: id, title, category, content
        """
        if self._doc_cache is None:
            self._doc_cache = self.db_init.get_all_documents()
            logger.info(f"Loaded {len(self._doc_cache)} documents from database")
        
        return self._doc_cache
    
    def get_document(self, doc_id: str) -> Dict:
        """
        Get single document by ID
        
        Args:
            doc_id: Document ID
        
        Returns:
            Document dictionary or None if not found
        """
        doc = self.db_init.get_document_by_id(doc_id)
        if doc:
            logger.debug(f"Retrieved document: {doc_id}")
        else:
            logger.warning(f"Document not found: {doc_id}")
        
        return doc
    
    def get_documents_by_category(self, category: str) -> List[Dict]:
        """
        Get documents by category
        
        Args:
            category: Document category (e.g., 'products', 'costs', 'safety', etc.)
        
        Returns:
            List of document dictionaries
        """
        docs = self.db_init.get_documents_by_category(category)
        logger.info(f"Retrieved {len(docs)} documents for category: {category}")
        
        return docs
    
    def get_document_count(self) -> int:
        """Get total number of documents in knowledge base"""
        return self.db_init.get_document_count()
    
    def refresh_cache(self):
        """Refresh document cache from database"""
        self._doc_cache = None
        logger.info("Document cache refreshed")


# Global knowledge base instance
_kb = None


def get_knowledge_base() -> KnowledgeBase:
    """Get singleton knowledge base instance"""
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
    
    return _kb


def get_all_documents() -> List[Dict]:
    """
    Convenience function to get all documents
    Used by rag_system.py
    
    Returns:
        List of document dictionaries
    """
    kb = get_knowledge_base()
    return kb.get_all_documents()


def get_document(doc_id: str) -> Dict:
    """
    Convenience function to get document by ID
    
    Args:
        doc_id: Document ID
    
    Returns:
        Document dictionary or None
    """
    kb = get_knowledge_base()
    return kb.get_document(doc_id)


def get_documents_by_category(category: str) -> List[Dict]:
    """
    Convenience function to get documents by category
    
    Args:
        category: Document category
    
    Returns:
        List of document dictionaries
    """
    kb = get_knowledge_base()
    return kb.get_documents_by_category(category)


if __name__ == "__main__":
    # Test knowledge base
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    kb = get_knowledge_base()
    
    print(f"\nTotal documents: {kb.get_document_count()}")
    print(f"\nDocument categories:")
    
    all_docs = kb.get_all_documents()
    categories = {}
    for doc in all_docs:
        cat = doc['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(doc['id'])
    
    for cat, doc_ids in sorted(categories.items()):
        print(f"  {cat}: {', '.join(doc_ids)}")
    
    print(f"\nSample document (account_types):")
    doc = kb.get_document('account_types')
    if doc:
        print(f"  Title: {doc['title']}")
        print(f"  Category: {doc['category']}")
        print(f"  Content preview: {doc['content'][:100]}...")
