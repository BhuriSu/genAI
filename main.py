from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import pandas as pd
import io
import json

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input models
class PromptRequest(BaseModel):
    prompt: str

# Response models
class AnalysisResponse(BaseModel):
    metrics: Dict
    summary: str
    trends: List[str]
    recommendations: List[str]

class TextResponse(BaseModel):
    text: str

class ImageResponse(BaseModel):
    imageUrl: str

class ContentResponse(BaseModel):
    content: str

# Financial Analysis Endpoint
@app.post("/api/analyze-reports", response_model=AnalysisResponse)
async def analyze_reports(files: List[UploadFile] = File(...)):
    try:
        # Initialize metrics dictionary
        metrics = {
            "revenue": {},
            "gross_margin": {},
            "net_income": {}
        }
        
        for file in files:
            # Read file content
            content = await file.read()
            
            # Process based on file type
            if file.filename.endswith('.csv'):
                df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            elif file.filename.endswith('.xlsx'):
                df = pd.read_excel(io.BytesIO(content))
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format")
                
            # Sample analysis logic (replace with your actual analysis)
            # This is just an example - you'd want to implement your actual analysis logic
            metrics["revenue"].update({
                "2023-Q1": 100000,
                "2023-Q2": 120000,
                "2023-Q3": 150000,
                "2023-Q4": 180000
            })
            metrics["gross_margin"].update({
                "2023-Q1": 70000,
                "2023-Q2": 85000,
                "2023-Q3": 100000,
                "2023-Q4": 120000
            })
            metrics["net_income"].update({
                "2023-Q1": 30000,
                "2023-Q2": 40000,
                "2023-Q3": 50000,
                "2023-Q4": 60000
            })

        return {
            "metrics": metrics,
            "summary": "Financial analysis shows steady growth across all metrics.",
            "trends": [
                "Revenue increased by 20% quarter over quarter",
                "Gross margin maintained at 70%",
                "Net income showed consistent improvement"
            ],
            "recommendations": [
                "Consider expanding market presence",
                "Invest in automation to improve margins",
                "Explore new revenue streams"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Text Generation Endpoints
@app.post("/api/generate/text", response_model=TextResponse)
async def generate_text(request: PromptRequest):
    try:
        # Implement your text generation logic here
        # This is a placeholder response
        generated_text = f"Generated text based on prompt: {request.prompt}"
        return {"text": generated_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/text/2D", response_model=ContentResponse)
async def generate_text_2d(request: PromptRequest):
    try:
        # Implement your 2D text generation logic here
        content = f"2D text content generated from prompt: {request.prompt}"
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/text/3D", response_model=ContentResponse)
async def generate_text_3d(request: PromptRequest):
    try:
        # Implement your 3D text generation logic here
        content = f"3D text content generated from prompt: {request.prompt}"
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Image Generation Endpoints
@app.post("/api/generate/image/2D", response_model=ImageResponse)
async def generate_image_2d(request: PromptRequest):
    try:
        # Implement your 2D image generation logic here
        # This should return a URL to the generated image
        image_url = f"http://example.com/generated-2d-image.jpg"  # Replace with actual image URL
        return {"imageUrl": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/image/3D", response_model=ImageResponse)
async def generate_image_3d(request: PromptRequest):
    try:
        # Implement your 3D image generation logic here
        # This should return a URL to the generated image
        image_url = f"http://example.com/generated-3d-image.jpg"  # Replace with actual image URL
        return {"imageUrl": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)