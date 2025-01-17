from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import PyPDF2
from transformers import pipeline
from io import BytesIO
import re
import logging
from textblob import TextBlob

# Initialize FastAPI app
app = FastAPI()

# Load summarizer model
try:
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
except Exception as e:
    logging.error(f"Error loading summarization model: {e}")
    raise

class URLInput(BaseModel):
    company: str
    url: str

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
        logging.error(f"Error extracting PDF text: {e}")
        raise HTTPException(status_code=400, detail="Error processing PDF file")

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
            except (ValueError, IndexError):
                continue
    
    return FinancialMetrics(**metrics)

def generate_summary(text: str) -> str:
    """Generate a summary of the text using BART."""
    try:
        max_chunk_length = 1024
        chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]
        
        summaries = []
        for chunk in chunks:
            summary = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        
        return " ".join(summaries)
    except Exception as e:
        logging.error(f"Error generating summary: {e}")
        return ""

def analyze_sentiment(text: str) -> Dict[str, float]:
    """Analyze sentiment and key phrases in the text using TextBlob."""
    blob = TextBlob(text)
    sentiment_score = blob.sentiment.polarity
    confidence = abs(sentiment_score)
    
    return {
        "sentiment_score": sentiment_score,
        "confidence": min(confidence, 1.0)
    }

@app.post("/api/analyze-reports")
async def analyze_reports(files: List[UploadFile] = File(...)) -> Dict:
    """Analyze multiple PDF reports and return comparative analysis."""
    results = {}
    
    for file in files:
        try:
            # Extract company name from filename (assuming format: company_originalname.pdf)
            company_name = file.filename.split('_')[0]
            
            content = await file.read()
            text = extract_text_from_pdf(content)
            metrics = extract_financial_metrics(text)
            summary = generate_summary(text)
            sentiment = analyze_sentiment(text)
            
            # Use company name instead of filename as key
            results[company_name] = {
                "metrics": metrics.model_dump(),
                "summary": summary,
                "sentiment": sentiment
            }
            
        except Exception as e:
            logging.error(f"Error processing {file.filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Error processing {file.filename}")

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
