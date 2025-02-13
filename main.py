from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
from enum import Enum
from functools import lru_cache
from dotenv import load_dotenv
import litellm
from logging.config import dictConfig
import logging
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Configure logging
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        }
    },
    "root": {
        "handlers": ["default"],
        "level": "INFO",
    }
}

dictConfig(logging_config)
logger = logging.getLogger(__name__)

class ModelType(str, Enum):
    """Enumeration of supported model types"""
    DEEPSEEK = "deepseek"
    FLUX = "flux"
    HUNYUAN = "hunyuan"

class Settings:
    """Application settings and configuration"""
    def __init__(self):
        self.app_name: str = "LLM API Service"
        self.api_keys: Dict[str, str] = {
            ModelType.DEEPSEEK: os.getenv("DEEPSEEK_API_KEY"),
            ModelType.FLUX: os.getenv("FLUX_API_KEY"),
            ModelType.HUNYUAN: os.getenv("HUNYUAN_API_KEY"),
        }
        self.api_bases: Dict[str, str] = {
            ModelType.DEEPSEEK: "https://api.deepseek.com/v1",
            ModelType.FLUX: "https://api.flux.ai/v1",
            ModelType.HUNYUAN: "https://api.hunyuan.com/v1",
        }
        self.model_configs: Dict[str, Dict[str, str]] = {
            ModelType.DEEPSEEK: {"model": "deepseekr1"},
            ModelType.FLUX: {"model": "flux-2d"},
            ModelType.HUNYUAN: {"model": "hunyuan3d-2"},
        }

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Configure LiteLLM router
def setup_litellm():
    """Configure LiteLLM with provider settings"""
    settings = get_settings()
    router_config = {}
    
    for model_type in ModelType:
        router_config[model_type] = {
            "model": settings.model_configs[model_type]["model"],
            "api_key": settings.api_keys[model_type],
            "api_base": settings.api_bases[model_type]
        }
    
    litellm.router = router_config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application"""
    # Startup: Initialize services
    logger.info("Starting up application...")
    setup_litellm()
    logger.info("Application started successfully")
    
    yield  # Application running
    
    # Shutdown: Clean up resources
    logger.info("Shutting down application...")
    # Add any cleanup code here if needed
    logger.info("Application shutdown complete")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="LLM API Service",
    description="A service for generating text and images using various LLM providers",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic models
class TextRequest(BaseModel):
    """Request model for text generation"""
    prompt: str = Field(..., description="The input prompt for text generation")
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional parameters for the model"
    )

    class Config:
        schema_extra = {
            "example": {
                "prompt": "Write a story about a space adventure",
                "parameters": {"temperature": 0.7, "max_tokens": 100}
            }
        }

class AnalyzeReportRequest(BaseModel):
    """Request model for report analysis"""
    report_text: str = Field(..., description="The report text to analyze")

class ErrorResponse(BaseModel):
    """Standard error response model"""
    detail: str

# Helper functions
async def generate_text_with_model(
    model_type: ModelType,
    request: TextRequest
) -> Dict[str, Any]:
    """Generic function for text generation with any model"""
    try:
        response = litellm.completion(
            model=model_type,
            messages=[{"role": "user", "content": request.prompt}],
            **(request.parameters or {})
        )
        return response
    except Exception as e:
        logger.error(f"Error generating text with {model_type}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating text: {str(e)}"
        )

# API routes
@app.post(
    "/api/generate/text",
    response_model=Dict[str, Any],
    responses={500: {"model": ErrorResponse}}
)
async def generate_text(request: TextRequest):
    """Generate text using DeepseekR1 model"""
    return await generate_text_with_model(ModelType.DEEPSEEK, request)

@app.post(
    "/api/generate/text/2D",
    response_model=Dict[str, Any],
    responses={500: {"model": ErrorResponse}}
)
async def generate_text_2d(request: TextRequest):
    """Generate 2D text using Flux"""
    return await generate_text_with_model(ModelType.FLUX, request)

@app.post(
    "/api/generate/text/3D",
    response_model=Dict[str, Any],
    responses={500: {"model": ErrorResponse}}
)
async def generate_text_3d(request: TextRequest):
    """Generate 3D text using Hunyuan"""
    return await generate_text_with_model(ModelType.HUNYUAN, request)

@app.post(
    "/api/generate/image/3D",
    response_model=Dict[str, Any],
    responses={500: {"model": ErrorResponse}}
)
async def generate_image_3d(request: TextRequest):
    """Generate 3D image using Hunyuan"""
    return await generate_text_with_model(ModelType.HUNYUAN, request)

@app.post(
    "/api/analyze-reports",
    response_model=Dict[str, Any],
    responses={500: {"model": ErrorResponse}}
)
async def analyze_reports(request: AnalyzeReportRequest):
    """Analyze reports and generate visualization recommendations"""
    # TODO: Implement report analysis functionality
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Report analysis functionality not implemented yet"
    )

if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"Failed to start FastAPI server: {e}")
