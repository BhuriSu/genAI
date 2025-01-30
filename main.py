from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
from datetime import datetime

app = FastAPI()

# API Models
class TextRequest(BaseModel):
    prompt: str
    parameters: Optional[dict] = None

class AnalyzeReportRequest(BaseModel):
    report_text: str
    metrics: Optional[list[str]] = None

# API client configuration
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/generate"
FLUX_API_URL = "https://api.flux.ai/v1/text2d"
HUNYUAN_API_URL = "https://api.hunyuan.com/v1"



async def call_external_api(url: str, headers: dict, payload: dict):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"External API error: {str(e)}")

@app.post("/api/generate/text")
async def generate_text(request: TextRequest):
    """Generate text using DeepseekR1 model"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": request.prompt,
        "model": "deepseekr1",
        **(request.parameters or {})
    }
    
    return await call_external_api(DEEPSEEK_API_URL, headers, payload)

@app.post("/api/generate/text/2D")
async def generate_text_2d(request: TextRequest):
    """Generate 2D text using Flux"""
    headers = {
        "Authorization": f"Bearer {FLUX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": request.prompt,
        "type": "2d",
        **(request.parameters or {})
    }
    
    return await call_external_api(FLUX_API_URL, headers, payload)

@app.post("/api/generate/text/3D")
async def generate_text_3d(request: TextRequest):
    """Generate 3D text using Hunyuan3D-2"""
    headers = {
        "Authorization": f"Bearer {HUNYUAN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": request.prompt,
        "model": "hunyuan3d-2",
        "mode": "text",
        **(request.parameters or {})
    }
    
    return await call_external_api(f"{HUNYUAN_API_URL}/generate", headers, payload)

@app.post("/api/generate/image/3D")
async def generate_image_3d(request: TextRequest):
    """Generate 3D image using Hunyuan3D-2"""
    headers = {
        "Authorization": f"Bearer {HUNYUAN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": request.prompt,
        "model": "hunyuan3d-2",
        "mode": "image",
        **(request.parameters or {})
    }
    
    return await call_external_api(f"{HUNYUAN_API_URL}/generate", headers, payload)

@app.post("/api/analyze-reports")
async def analyze_reports(request: AnalyzeReportRequest):
    """Custom implementation for report analysis"""
    try:
        # Example implementation of report analysis
        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "word_count": len(request.report_text.split()),
            "metrics": {}
        }
        
        # Process requested metrics
        if request.metrics:
            for metric in request.metrics:
                if metric == "sentiment":
                    # Example sentiment analysis (replace with your implementation)
                    analysis_result["metrics"]["sentiment"] = "positive"
                elif metric == "key_topics":
                    # Example topic extraction (replace with your implementation)
                    analysis_result["metrics"]["key_topics"] = ["topic1", "topic2"]
                # Add more metric implementations as needed
        
        return analysis_result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)