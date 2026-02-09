"""
Vector Store Service for NEXUS

ChromaDB-based vector storage for semantic search capabilities.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config


class VectorStore:
    """
    ChromaDB vector store for semantic search.
    
    Stores activity embeddings for similarity-based retrieval.
    """
    
    _instance = None
    _client = None
    _collection = None
    
    def __new__(cls):
        """Singleton pattern to reuse connection."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize ChromaDB client and collection."""
        if VectorStore._client is None:
            VectorStore._client = chromadb.PersistentClient(
                path=str(Config.CHROMA_DIR),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            VectorStore._collection = VectorStore._client.get_or_create_collection(
                name="nexus_memories",
                metadata={"description": "NEXUS activity memories for semantic search"}
            )
            
            print("[VectorStore] Initialized")
    
    @property
    def collection(self):
        """Get the ChromaDB collection."""
        return VectorStore._collection
    
    async def add_embedding(self, id: str, embedding: List[float], metadata: Dict):
        """
        Add an embedding to the vector store.
        
        Args:
            id: Unique identifier (usually activity ID)
            embedding: Vector embedding
            metadata: Associated metadata (activity, tags, etc.)
        """
        # Create document text from metadata
        document = f"{metadata.get('activity', '')} {metadata.get('extracted_text', '')}"
        
        # Prepare metadata for ChromaDB (must be flat dict with basic types)
        chroma_metadata = {
            'app_name': str(metadata.get('app_name', '')),
            'tags': ','.join(metadata.get('tags', [])) if isinstance(metadata.get('tags'), list) else str(metadata.get('tags', '')),
            'priority': str(metadata.get('priority', 'low')),
            'activity': str(metadata.get('activity', ''))[:500]  # Truncate long text
        }
        
        try:
            self.collection.add(
                ids=[id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[chroma_metadata]
            )
        except Exception as e:
            # Handle duplicate ID by updating
            if "already exists" in str(e).lower():
                self.collection.update(
                    ids=[id],
                    embeddings=[embedding],
                    documents=[document],
                    metadatas=[chroma_metadata]
                )
            else:
                print(f"[VectorStore] Error adding embedding: {e}")
    
    async def semantic_search(self, query_embedding: List[float], limit: int = 10) -> List[Dict]:
        """
        Search for similar activities.
        
        Args:
            query_embedding: Query vector
            limit: Maximum results to return
            
        Returns:
            List of matching results with distance scores
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i, activity_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'activity_id': activity_id,
                        'distance': results['distances'][0][i] if results['distances'] else 0,
                        'document': results['documents'][0][i] if results['documents'] else '',
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"[VectorStore] Search error: {e}")
            return []
    
    async def search_by_text(self, query_text: str, limit: int = 10) -> List[Dict]:
        """
        Search using text query (ChromaDB will handle embedding).
        
        Args:
            query_text: Text query
            limit: Maximum results
            
        Returns:
            List of matching results
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=limit,
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i, activity_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'activity_id': activity_id,
                        'distance': results['distances'][0][i] if results['distances'] else 0,
                        'document': results['documents'][0][i] if results['documents'] else '',
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"[VectorStore] Text search error: {e}")
            return []
    
    def get_count(self) -> int:
        """Get number of embeddings in store."""
        return self.collection.count()
    
    def delete_embedding(self, id: str):
        """Delete an embedding by ID."""
        try:
            self.collection.delete(ids=[id])
        except Exception as e:
            print(f"[VectorStore] Delete error: {e}")
    
    def reset(self):
        """Reset the entire collection (danger!)."""
        VectorStore._client.delete_collection("nexus_memories")
        VectorStore._collection = VectorStore._client.get_or_create_collection(
            name="nexus_memories",
            metadata={"description": "NEXUS activity memories for semantic search"}
        )
        print("[VectorStore] Collection reset")
