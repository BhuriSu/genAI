from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import PyPDF2
from transformers import pipeline
from io import BytesIO
import re
import logging
import plotly.graph_objs as go
import plotly.io as pio
import numpy as np

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
    gross_profit: float
    gross_margin: float
    operating_expenses: float
    operating_income: float
    operating_margin: float
    net_income: float

def extract_text_from_pdf(pdf_file: bytes) -> str:
    """Extract text from PDF bytes."""
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        # Add debug logging
        logging.info(f"Extracted text length: {len(text)}")
        logging.info(f"First 500 characters: {text[:500]}")
        
        return text
    except Exception as e:
        logging.error(f"Error extracting PDF text: {e}")
        raise HTTPException(status_code=400, detail=str(e))

def extract_financial_metrics(text: str) -> FinancialMetrics:
    """
    Extract key financial metrics from text with enhanced pattern matching.
    Handles various cases of revenue, gross margin, and net income.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        FinancialMetrics: Extracted financial metrics
    """
    metrics = {
        "revenue": 0.0,
        "gross_profit": 0.0,
        "gross_margin": 0.0,
        "operating_expenses": 0.0,
        "operating_income": 0.0,
        "operating_margin": 0.0,
        "net_income": 0.0
    }
    
    # Convert text to lowercase for case-insensitive matching
    text = text.lower()
    
    # Comprehensive patterns for each metric
    patterns = {
        "revenue": [
            r"(?:total\s+)?revenues?\s*(?:of|:)?\s*\$?\s*([-\(]?\d+(?:\.\d+)?)\s*(billion|million|b|m)?",
            r"(?:total\s+)?revenues?\s*(?:were|was|reached|totaled)?\s*\$?\s*([-\(]?\d+(?:\.\d+)?)\s*(billion|million|b|m)?",
            r"(?:reported\s+)?revenues?\s*(?:of|:)?\s*\$?\s*([-\(]?\d+(?:\.\d+)?)\s*(billion|million|b|m)?",
            r"(?:total|reported)\s+revenues?\s*increased.*?\$?\s*([-\(]?\d+(?:\.\d+)?)\s*(billion|million|b|m)?",
            r"revenue\s*\$?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|b|m)?",  # Simple revenue pattern
        ],
        
        "gross_profit": [
            r"gross\s+profit\s*(?:of|:)?\s*\$?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|b|m)?",
            r"gross\s+profit\s*(?:was|reached|totaled)?\s*\$?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|b|m)?",
        ],
        
        "gross_margin": [
            r"gross\s+margin.*?([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*%",
            r"gross\s+margin\s*(?:of|:)?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*%",
            r"gross\s+margin\s*(?:was|reached|totaled)?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*%",
            r"gross\s+margin\s*increased.*?([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*%",
        ],
        
        "operating_expenses": [
            r"operating\s+expenses?\s*(?:of|:)?\s*\$?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|b|m)?",
            r"operating\s+expenses?\s*(?:were|was|reached|totaled)?\s*\$?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|b|m)?",
        ],
        
        "operating_income": [
            r"operating\s+income\s*(?:of|:)?\s*\$?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|b|m)?",
            r"operating\s+income\s*(?:was|reached|totaled)?\s*\$?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|b|m)?",
        ],
        
        "operating_margin": [
            r"operating\s+margin.*?([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*%",
            r"operating\s+margin\s*(?:of|:)?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*%",
            r"operating\s+margin\s*(?:was|reached|totaled)?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*%",
            r"operating\s+margin\s*increased.*?([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*%",
        ],
        
        "net_income": [
            r"(?:adjusted\s+)?net\s+(?:income|profit|earnings).*?\$?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|b|m)?",
            r"(?:reported\s+)?net\s+(?:income|profit|earnings).*?\$?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|b|m)?",
            r"net\s+(?:income|profit|earnings)\s*(?:of|:)?\s*\$?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|b|m)?",
            r"net\s+(?:income|profit|earnings)\s+(?:was|reached|totaled)?\s*\$?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|b|m)?",
            r"Net income\s*\$?\s*([-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|b|m)?"
        ]
    }
    
    # Value multipliers for different units
    multipliers = {
        'billion': 1000, 'b': 1000,
        'million': 1, 'm': 1,
        'thousand': 0.001, 'k': 0.001
    }
    
    # Dollar amount pattern for additional checking
    dollar_pattern = r'\$\s*((?:[\d,]+(?:\.\d+)?))'
    
    for metric, metric_patterns in patterns.items():
        for pattern in metric_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    if metric in ["gross_margin", "operating_margin"]:
                        value = float(match.group(1).replace(',', '').replace('(', '-').replace(')', ''))
                    else:
                        value = float(match.group(1).replace(',', '').replace('(', '-').replace(')', ''))
                        if len(match.groups()) > 1 and match.group(2):
                            unit = match.group(2).lower()
                            multiplier = multipliers.get(unit, 1)
                            value *= multiplier
                    
                    # Store the first non-zero value found or the larger value if we find multiple
                    if value != 0 and (metrics[metric] == 0 or value > metrics[metric]):
                        metrics[metric] = value
                        logging.info(f"Matched {metric} with value {value} using pattern: {pattern}")
                        
                except (ValueError, IndexError) as e:
                    logging.warning(f"Error parsing {metric}: {e}")
                    continue
    
    # Additional check for dollar amounts if net income is still zero
    if metrics["net_income"] == 0:
        dollar_matches = re.finditer(dollar_pattern, text)
        largest_dollar_amount = 0
        for match in dollar_matches:
            try:
                value = float(match.group(1).replace(',', ''))
                if value > largest_dollar_amount:
                    largest_dollar_amount = value
            except (ValueError, IndexError):
                continue
        if largest_dollar_amount > 1000:  # Threshold for considering it as net income
            metrics["net_income"] = largest_dollar_amount
            logging.info(f"Found net income from dollar amount: {largest_dollar_amount}")
    
    return FinancialMetrics(**metrics)

def generate_plotly_visualizations(metrics: Dict[str, Dict[str, float]]) -> Dict[str, Dict]:
    """
    Generate Plotly visualizations for financial metrics.
    
    Args:
        metrics (Dict[str, Dict[str, float]]): Dictionary of financial metrics for each company.
        
    Returns:
        Dict[str, Dict]: Dictionary of Plotly JSON objects for each visualization.
    """
    visualizations = {}
    
    try:
        companies = list(metrics["revenue"].keys())
        
        # Revenue Bar Chart
        revenue_bar = go.Figure(
            data=[go.Bar(x=companies, y=list(metrics["revenue"].values()), name="Revenue")],
            layout=go.Layout(title="Revenue Comparison", xaxis_title="Companies", yaxis_title="Revenue (in millions)")
        )
        visualizations["revenue"] = revenue_bar.to_dict()
        
        # Gross Margin Line Chart
        gross_margin_line = go.Figure(
            data=[go.Scatter(x=companies, y=list(metrics["gross_margin"].values()), mode="lines+markers", name="Gross Margin")],
            layout=go.Layout(title="Gross Margin Comparison", xaxis_title="Companies", yaxis_title="Gross Margin (%)")
        )
        visualizations["gross_margin"] = gross_margin_line.to_dict()
        
        # Net Income Pie Chart
        net_income_pie = go.Figure(
            data=[go.Pie(labels=companies, values=list(metrics["net_income"].values()), name="Net Income")],
            layout=go.Layout(title="Net Income Distribution")
        )
        visualizations["net_income"] = net_income_pie.to_dict()
        
    except Exception as e:
        logger.error(f"Error generating Plotly visualizations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate visualizations")
    
    return visualizations

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
                "gross_profit": {k: v["metrics"]["gross_profit"] for k, v in results.items()},
                "gross_margin": {k: v["metrics"]["gross_margin"] for k, v in results.items()},
                "operating_expenses": {k: v["metrics"]["operating_expenses"] for k, v in results.items()},
                "operating_income": {k: v["metrics"]["operating_income"] for k, v in results.items()},
                "operating_margin": {k: v["metrics"]["operating_margin"] for k, v in results.items()},
                "net_income": {k: v["metrics"]["net_income"] for k, v in results.items()}
            }
        }
        
        # Generate Plotly visualizations
        visualizations = generate_plotly_visualizations(comparative_analysis["metrics"])
        
        return {
            "comparative_analysis": comparative_analysis,
            "visualizations": visualizations
        }
        
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