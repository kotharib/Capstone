"""
RAG System: Retrieval-Augmented Generation
Implements embeddings, vector storage, and semantic search
"""

import logging
from typing import List, Dict, Tuple, Any
import re
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    raise ImportError("Please install chromadb: pip install chromadb")

from config import Config
from knowledge_base import get_all_documents

# ============================================================================
# Logging Setup
# ============================================================================

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("rag_system.log", mode='a')
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
# Text Chunking
# ============================================================================

class TextChunker:
    """Split documents into chunks for embedding"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        """
        Args:
            chunk_size: Characters per chunk
            overlap: Character overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.logger = logging.getLogger(__name__)
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Full text to chunk
            metadata: Additional metadata for each chunk
        
        Returns:
            List of chunks with content and metadata
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # Split by sentences first
        sentences = self._split_sentences(text)
        chunks = []
        current_chunk = ""
        chunk_num = 0
        
        for sentence in sentences:
            # Add to current chunk if it fits
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence
            else:
                # Save current chunk if not empty
                if current_chunk.strip():
                    chunk_num += 1
                    chunks.append({
                        "content": current_chunk.strip(),
                        "chunk_id": f"chunk_{chunk_num}",
                        "start_char": len("\n".join([c["content"] for c in chunks])),
                        "metadata": metadata or {}
                    })
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else ""
                current_chunk = overlap_text + sentence
        
        # Add final chunk
        if current_chunk.strip():
            chunk_num += 1
            chunks.append({
                "content": current_chunk.strip(),
                "chunk_id": f"chunk_{chunk_num}",
                "metadata": metadata or {}
            })
        
        self.logger.info(f"Split text ({len(text)} chars) into {len(chunks)} chunks")
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences preserving structure"""
        # Split on periods, question marks, exclamation marks
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Keep empty lines and preserve formatting
        sentences = [s.strip() + " " for s in sentences if s.strip()]
        
        return sentences


# ============================================================================
# Vector Store & Retrieval
# ============================================================================

class RAGSystem:
    """
    Retrieval-Augmented Generation system
    Uses embeddings for semantic search
    """
    
    def __init__(self, collection_name: str = "banking_docs"):
        """
        Initialize RAG system with Chroma vector store
        
        Args:
            collection_name: Name of vector collection
        """
        self.collection_name = collection_name
        self.chunker = TextChunker(chunk_size=500, overlap=100)
        
        # Initialize Chroma
        try:
            self.client = chromadb.Client(
                Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory="./chroma_db",
                    anonymized_telemetry=False
                )
            )
            logger.info(f"Chroma initialized with persistent storage")
        except Exception as e:
            logger.warning(f"Chroma persistent storage failed: {e}, using in-memory")
            self.client = chromadb.Client()
        
        self.collection = None
        self.doc_chunks = {}
        
        logger.info(f"RAGSystem initialized for collection: {collection_name}")
    
    def ingest_documents(self) -> int:
        """
        Ingest all documents from knowledge base into vector store
        
        Returns:
            Number of chunks ingested
        """
        logger.info("Starting document ingestion...")
        
        documents = get_all_documents()
        all_chunks = []
        chunk_id = 0
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(self.collection_name)
            logger.info(f"Using existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Banking knowledge base"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
        
        # Chunk all documents
        for doc in documents:
            chunks = self.chunker.chunk_text(
                doc["content"],
                metadata={"source": doc["id"], "title": doc["title"]}
            )
            
            for chunk in chunks:
                chunk_id += 1
                unique_id = f"{doc['id']}_{chunk['chunk_id']}"
                
                all_chunks.append({
                    "id": unique_id,
                    "content": chunk["content"],
                    "metadata": {
                        "source": doc["id"],
                        "title": doc["title"],
                        "chunk_index": chunk['chunk_id']
                    }
                })
                
                self.doc_chunks[unique_id] = chunk["content"]
        
        # Add to collection using OpenAI embeddings
        if all_chunks:
            ids = [c["id"] for c in all_chunks]
            contents = [c["content"] for c in all_chunks]
            metadatas = [c["metadata"] for c in all_chunks]
            
            # Chroma will automatically embed using default (OpenAI if API key available)
            self.collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas
            )
            
            logger.info(f"Ingested {len(all_chunks)} chunks from {len(documents)} documents")
        
        return len(all_chunks)
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using semantic search
        
        Args:
            query: User query
            top_k: Number of top results to return
        
        Returns:
            List of relevant document chunks with scores
        """
        if not self.collection:
            logger.warning("Collection not initialized, returning empty results")
            return []
        
        try:
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # Format results
            retrieved = []
            if results and results['ids'] and len(results['ids']) > 0:
                for i, doc_id in enumerate(results['ids'][0]):
                    content = results['documents'][0][i] if results['documents'] else ""
                    distance = results['distances'][0][i] if results['distances'] else 0
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    
                    # Convert distance to similarity score (0-1, higher is better)
                    similarity = 1 / (1 + distance) if distance >= 0 else 0
                    
                    retrieved.append({
                        "doc_id": doc_id,
                        "content": content,
                        "similarity": similarity,
                        "distance": distance,
                        "source": metadata.get("source", "unknown"),
                        "title": metadata.get("title", "")
                    })
            
            logger.info(f"Retrieved {len(retrieved)} documents for query: {query[:50]}")
            return retrieved
        
        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            return []
    
    def format_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into context string for LLM
        
        Args:
            retrieved_docs: List of retrieved documents
        
        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return ""
        
        context = "RETRIEVED CONTEXT:\n\n"
        for i, doc in enumerate(retrieved_docs, 1):
            context += f"[Source {i}: {doc['source']} - Similarity: {doc['similarity']:.2%}]\n"
            context += f"{doc['content'][:300]}...\n\n"
        
        return context


# ============================================================================
# Initialization & Testing
# ============================================================================

def initialize_rag_system() -> RAGSystem:
    """Initialize and populate RAG system"""
    rag = RAGSystem()
    rag.ingest_documents()
    return rag


if __name__ == "__main__":
    logger.info("Testing RAG System")
    
    # Initialize
    rag = initialize_rag_system()
    
    # Test retrieval
    test_queries = [
        "What documents do I need to open an account?",
        "How much money is FDIC insured?",
        "What are the overdraft protection options?"
    ]
    
    for query in test_queries:
        logger.info(f"\n{'='*80}")
        logger.info(f"Query: {query}")
        logger.info(f"{'='*80}")
        
        results = rag.retrieve(query, top_k=2)
        
        for i, result in enumerate(results, 1):
            logger.info(f"[Result {i}] Source: {result['source']}")
            logger.info(f"  Similarity: {result['similarity']:.2%}")
            logger.info(f"  Content: {result['content'][:200]}...")
