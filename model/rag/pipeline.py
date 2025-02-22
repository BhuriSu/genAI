# model/rag/pipeline.py
from haystack import Pipeline
from haystack.nodes import PreProcessor, Retriever
from typing import List, Dict
from .document_store import VectorStore
from ..config import RAGConfig

class RAGPipeline:
    def __init__(self, vector_store: VectorStore, config: RAGConfig):
        self.config = config
        self.vector_store = vector_store
        self.pipeline = self._create_pipeline()
    
    def _create_pipeline(self) -> Pipeline:
        preprocessor = PreProcessor()
        retriever = Retriever(
            document_store=self.vector_store.document_store,
            top_k=self.config.top_k
        )
        
        pipeline = Pipeline()
        pipeline.add_node(component=preprocessor, name="preprocessor", inputs=["Query"])
        pipeline.add_node(component=retriever, name="retriever", inputs=["preprocessor"])
        
        return pipeline
    
    def run(self, query: str) -> Dict:
        return self.pipeline.run(query=query)