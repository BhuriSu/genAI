# model/rag_model.py
from typing import Dict, List
from haystack import Pipeline
from haystack.nodes import RAGenerator, PromptNode
from haystack.document_stores import PostgreSQLDocumentStore

class RAGModel:
    def __init__(self):
        self.document_store = PostgreSQLDocumentStore(
            host="localhost",
            port=5432,
            username="user",
            password="pass",
            database="financial_reports",
            embedding_dim=384,
            use_gpu=False
        )
        
        self.pipeline = self._setup_pipeline()
    
    def _setup_pipeline(self) -> Pipeline:
        """Setup RAG pipeline"""
        retriever = self.document_store.get_retriever()
        generator = PromptNode(
            model_name_or_path="anthropic/claude-3-opus-20240229",
            api_key="your-key"
        )
        
        pipeline = Pipeline()
        pipeline.add_node(component=retriever, name="Retriever", inputs=["Query"])
        pipeline.add_node(component=generator, name="Generator", inputs=["Retriever"])
        
        return pipeline
    
    def query(self, question: str) -> Dict:
        """Query the RAG pipeline"""
        return self.pipeline.run(query=question)