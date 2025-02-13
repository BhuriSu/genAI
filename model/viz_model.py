# model/viz_model.py
from typing import Dict, Any
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class VisualizationModel:
    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained("your_finetuned_model")
        self.tokenizer = AutoTokenizer.from_pretrained("your_finetuned_model")
    
    def generate_visualization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visualization specification"""
        prompt = self._prepare_prompt(data)
        
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs)
        viz_spec = self.tokenizer.decode(outputs[0])
        
        return self._parse_viz_spec(viz_spec)
    
    def _prepare_prompt(self, data: Dict[str, Any]) -> str:
        """Prepare prompt for visualization generation"""
        # Convert data to prompt format
        return f"Generate visualization for: {data}"
    
    def _parse_viz_spec(self, spec: str) -> Dict[str, Any]:
        """Parse model output into visualization specification"""
        # Parse and validate visualization spec
        return {"type": "line_chart", "data": spec}