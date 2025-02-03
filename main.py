from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import litellm

app = FastAPI()

# Load API keys from environment variables
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
FLUX_API_KEY = os.getenv("FLUX_API_KEY")
HUNYUAN_API_KEY = os.getenv("HUNYUAN_API_KEY")

# Configure LiteLLM to use multiple providers
litellm.router = {
    "deepseek": {"model": "deepseekr1", "api_key": DEEPSEEK_API_KEY, "api_base": "https://api.deepseek.com/v1"},
    "flux": {"model": "flux-2d", "api_key": FLUX_API_KEY, "api_base": "https://api.flux.ai/v1"},
    "hunyuan": {"model": "hunyuan3d-2", "api_key": HUNYUAN_API_KEY, "api_base": "https://api.hunyuan.com/v1"},
}

# API Models
class TextRequest(BaseModel):
    prompt: str
    parameters: Optional[dict] = None

class AnalyzeReportRequest(BaseModel):
    report_text: str


@app.post("/api/generate/text")
async def generate_text(request: TextRequest):
    """Generate text using DeepseekR1 model via LiteLLM"""
    try:
        response = litellm.completion(
            model="deepseek",
            messages=[{"role": "user", "content": request.prompt}],
            **(request.parameters or {})
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/text/2D")
async def generate_text_2d(request: TextRequest):
    """Generate 2D text using Flux"""
    try:
        response = litellm.completion(
            model="flux",
            messages=[{"role": "user", "content": request.prompt}],
            **(request.parameters or {})
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/text/3D")
async def generate_text_3d(request: TextRequest):
    """Generate 3D text using Hunyuan"""
    try:
        response = litellm.completion(
            model="hunyuan",
            messages=[{"role": "user", "content": request.prompt}],
            **(request.parameters or {})
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/image/3D")
async def generate_image_3d(request: TextRequest):
    """Generate 3D image using Hunyuan"""
    try:
        response = litellm.completion(
            model="hunyuan",
            messages=[{"role": "user", "content": request.prompt}],
            **(request.parameters or {})
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-reports")
async def analyze_reports(request: AnalyzeReportRequest):
    # 1. Get data from your PostgreSQL database
    # 2. Pass to your fine-tuned model
    # 3. Model generates visualization recommendation
    # 4. Return the visualization spec (e.g., as JSON)
    return {}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
