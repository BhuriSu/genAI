# model/rag/retriever.py

from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from .document_store import PGVectorStore
from ..config import RAGConfig

class SemanticRetriever:
    def __init__(self, vector_store: PGVectorStore, config: RAGConfig):
        self.vector_store = vector_store
        self.config = config
        # Use a financial-specific model if available
        self.encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
    async def retrieve(
        self, 
        query: str, 
        filters: Optional[Dict] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents based on semantic similarity.
        
        Args:
            query: User query string
            filters: Optional metadata filters (e.g., {'date': '2024-01-01'})
            top_k: Optional override for number of results
            
        Returns:
            List of relevant documents with similarity scores and metadata
        """
        # Pre-process query
        processed_query = self._preprocess_query(query)
        
        # Get base results
        results = await self._get_base_results(processed_query, top_k)
        
        # Apply filters if specified
        if filters:
            results = self._apply_filters(results, filters)
            
        # Apply cross-encoder reranking for more accurate results
        if len(results) > 1:
            results = await self._rerank_results(results, processed_query)
            
        # Post-process results
        processed_results = self._postprocess_results(results)
        
        return processed_results

    def _preprocess_query(self, query: str) -> str:
        """
        Clean and enhance the query for better retrieval.
        """
        # Remove special characters
        query = ''.join(char for char in query if char.isalnum() or char.isspace())
        
        # Convert to lowercase
        query = query.lower()
        
        # Add financial context if needed
        if any(term in query for term in ['stock', 'price', 'market']):
            query += " financial market analysis"
            
        return query

    async def _get_base_results(
        self, 
        query: str, 
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get initial results from vector store.
        """
        k = top_k or self.config.top_k
        results = await self.vector_store.query_similar(query, k)
        
        # Ensure we have minimum required results
        if len(results) < k:
            # Try query expansion
            expanded_results = await self._expand_query(query, k - len(results))
            results.extend(expanded_results)
            
        return results

    def _apply_filters(
        self, 
        results: List[Dict[str, Any]], 
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply metadata filters to results.
        """
        filtered_results = []
        
        for result in results:
            metadata = result.get('meta', {})
            
            # Check all filter conditions
            matches_all = True
            for key, value in filters.items():
                if key == 'date':
                    # Handle date range filters
                    doc_date = datetime.fromisoformat(metadata.get(key, ''))
                    filter_date = datetime.fromisoformat(value)
                    if doc_date < filter_date:
                        matches_all = False
                        break
                elif metadata.get(key) != value:
                    matches_all = False
                    break
            
            if matches_all:
                filtered_results.append(result)
                
        return filtered_results

    async def _rerank_results(
        self, 
        results: List[Dict[str, Any]], 
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Rerank results using additional criteria.
        """
        for result in results:
            # Calculate relevance score
            relevance = self._calculate_relevance(result, query)
            
            # Calculate recency score
            recency = self._calculate_recency(result)
            
            # Calculate final score
            result['final_score'] = (0.7 * relevance) + (0.3 * recency)
        
        # Sort by final score
        return sorted(results, key=lambda x: x['final_score'], reverse=True)

    def _calculate_relevance(self, result: Dict[str, Any], query: str) -> float:
        """
        Calculate content relevance score.
        """
        # Base similarity score
        relevance = result.get('similarity', 0.0)
        
        # Boost if title matches query terms
        if 'title' in result.get('meta', {}):
            title_terms = set(result['meta']['title'].lower().split())
            query_terms = set(query.lower().split())
            term_overlap = len(title_terms & query_terms)
            relevance += 0.1 * term_overlap
            
        return min(1.0, relevance)  # Cap at 1.0

    def _calculate_recency(self, result: Dict[str, Any]) -> float:
        """
        Calculate recency score based on document age.
        """
        if 'date' not in result.get('meta', {}):
            return 0.5  # Default score if no date
            
        doc_date = datetime.fromisoformat(result['meta']['date'])
        now = datetime.now()
        age_days = (now - doc_date).days
        
        # Exponential decay based on age
        decay_factor = 0.99  # Adjust this to control decay rate
        recency = decay_factor ** age_days
        
        return recency

    async def _expand_query(
        self, 
        query: str, 
        needed_results: int
    ) -> List[Dict[str, Any]]:
        """
        Expand query to get more results if needed.
        """
        # Add related financial terms
        expanded_terms = []
        if 'stock' in query:
            expanded_terms.extend(['equity', 'shares'])
        if 'price' in query:
            expanded_terms.extend(['value', 'cost'])
            
        if not expanded_terms:
            return []
            
        expanded_query = f"{query} {' '.join(expanded_terms)}"
        return await self.vector_store.query_similar(expanded_query, needed_results)

    def _postprocess_results(
        self, 
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Final processing of results before returning.
        """
        processed_results = []
        
        for result in results:
            # Extract key information
            processed_result = {
                'content': result['content'],
                'similarity': result.get('similarity', 0.0),
                'metadata': result.get('meta', {}),
                'score': result.get('final_score', result.get('similarity', 0.0))
            }
            
            # Add snippet if content is long
            if len(result['content']) > 200:
                processed_result['snippet'] = result['content'][:200] + '...'
                
            processed_results.append(processed_result)
            
        return processed_results