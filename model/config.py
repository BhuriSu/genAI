# model/config.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMConfig:
    model_name: str = "meta-llama/Llama-2-7b"
    max_length: int = 512
    batch_size: int = 8
    learning_rate: float = 2e-5
    num_epochs: int = 3
    gradient_checkpointing: bool = True

@dataclass
class RAGConfig:
    haystack_pipeline_name: str = "query_pipeline"
    top_k: int = 5
    similarity_threshold: float = 0.7
    document_store_url: str = "postgresql://user:pass@localhost:5432/vector_db"

@dataclass
class VisualizationConfig:
    default_chart_type: str = "line"
    theme: str = "dark"
    max_data_points: int = 1000