# model/llm/inference.py
import torch

class LLMInference:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
    
    @torch.no_grad()
    def generate_response(self, prompt: str, max_length: int = 512) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True)
        outputs = self.model.generate(
            **inputs,
            max_length=max_length,
            num_return_sequences=1,
            temperature=0.7
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
