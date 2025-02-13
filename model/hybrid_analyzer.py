# model/hybrid_analyzer.py
from typing import Dict, Any
from .rag_model import RAGModel
from .viz_model import VisualizationModel

class HybridAnalyzer:
    def __init__(self):
        self.rag_model = RAGModel()
        self.viz_model = VisualizationModel()
    
    def analyze(self, query: str, output_format: str = "text") -> Dict[str, Any]:
        """Perform hybrid analysis"""
        # Get context from RAG
        rag_result = self.rag_model.query(query)
        
        if output_format == "visualization":
            # Generate visualization
            viz_spec = self.viz_model.generate_visualization(rag_result)
            return {
                "visualization": viz_spec,
                "context": rag_result
            }
        else:
            return {"text_analysis": rag_result}