from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import PyPDF2
from transformers import pipeline
from io import BytesIO
import re
import logging
from textblob import TextBlob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:5173",    # Vite default
    "http://localhost:3000",    # Alternative development port
    "http://127.0.0.1:5173",   # Alternative localhost
    "http://127.0.0.1:3000",   # Alternative localhost
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Load summarizer model
try:
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
except Exception as e:
    logger.error(f"Error loading summarization model: {e}")
    raise

class FinancialMetrics(BaseModel):
    revenue: float
    gross_margin: float
    net_income: float

def extract_text_from_pdf(pdf_file: bytes) -> str:
    """Extract text from PDF bytes."""
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        raise HTTPException(status_code=400, detail=str(e))

def extract_financial_metrics(text: str) -> FinancialMetrics:
    """Extract key financial metrics from text."""
    metrics = {
        "revenue": 0.0,
        "gross_margin": 0.0,
        "net_income": 0.0
    }
    
    patterns = {
        "revenue": r"revenue.*?\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)?",
        "gross_margin": r"gross margin.*?([\d,]+(?:\.\d+)?)\s*%",
        "net_income": r"net income.*?\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)?"
    }
    
    for metric, pattern in patterns.items():
        matches = re.finditer(pattern, text.lower())
        for match in matches:
            try:
                value = float(match.group(1).replace(',', ''))
                if "billion" in match.group(0).lower():
                    value *= 1000
                metrics[metric] = value
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing {metric}: {e}")
                continue
    
    return FinancialMetrics(**metrics)

@app.post("/api/analyze-reports")
async def analyze_reports(files: List[UploadFile] = File(...)) -> Dict:
    """Analyze multiple PDF reports and return comparative analysis."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    results = {}
    
    try:
        for file in files:
            if not file.filename.endswith('.pdf'):
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} is not a PDF"
                )
            
            content = await file.read()
            text = extract_text_from_pdf(content)
            metrics = extract_financial_metrics(text)
            
            company_name = file.filename.split('.')[0]
            results[company_name] = {
                "metrics": metrics.model_dump()
            }
        
        comparative_analysis = {
            "metrics": {
                "revenue": {k: v["metrics"]["revenue"] for k, v in results.items()},
                "gross_margin": {k: v["metrics"]["gross_margin"] for k, v in results.items()},
                "net_income": {k: v["metrics"]["net_income"] for k, v in results.items()}
            }
        }
        
        return {"comparative_analysis": comparative_analysis}
        
    except Exception as e:
        logger.error(f"Error processing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")