# model/rag/document_store.py
from typing import List, Dict, Any
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from ..config import RAGConfig

class PGVectorStore:
    def __init__(self, config: RAGConfig):
        self.config = config
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.conn = psycopg2.connect(config.document_store_url)
        register_vector(self.conn)
        self._initialize_tables()
    
    def _initialize_tables(self):
        with self.conn.cursor() as cur:
            # Create extension if not exists
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # Create documents table with vector support
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    embedding vector(384),
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create vector index
            cur.execute("""
                CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                ON documents 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            
            self.conn.commit()
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        # Encode documents
        texts = [doc["content"] for doc in documents]
        embeddings = self.encoder.encode(texts)
        
        # Prepare data for insertion
        data = [
            (
                doc["content"],
                embedding.tolist(),
                doc.get("meta", {})
            )
            for doc, embedding in zip(documents, embeddings)
        ]
        
        with self.conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO documents (content, embedding, metadata)
                VALUES %s
                """,
                data,
                template="(%s, %s::vector, %s::jsonb)"
            )
            self.conn.commit()
    
    def query_similar(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        if top_k is None:
            top_k = self.config.top_k
            
        # Encode query
        query_embedding = self.encoder.encode(query)
        
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    content,
                    metadata,
                    1 - (embedding <=> %s::vector) as similarity
                FROM documents
                WHERE 1 - (embedding <=> %s::vector) > %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (
                    query_embedding.tolist(),
                    query_embedding.tolist(),
                    self.config.similarity_threshold,
                    query_embedding.tolist(),
                    top_k
                )
            )
            
            results = cur.fetchall()
            
            return [
                {
                    "content": content,
                    "meta": metadata,
                    "similarity": float(similarity)
                }
                for content, metadata, similarity in results
            ]