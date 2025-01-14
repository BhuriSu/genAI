# Backend (Python)
from fastapi import FastAPI, HTTPException
import requests
import pdfplumber
import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict
import PyPDF2
import io
import numpy as np

class FinancialReportAnalyzer:
    def __init__(self):
        self.reports_data = {}
        
    async def fetch_pdf(self, url: str, company_name: str):
        """Fetch PDF from URL and extract text"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Read PDF content
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text()
                
            # Store raw text
            self.reports_data[company_name] = {
                'raw_text': text_content,
                'metrics': self.extract_financial_metrics(text_content)
            }
            
            return {"status": "success", "message": f"Successfully processed {company_name} report"}
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    def extract_financial_metrics(self, text: str) -> Dict:
        """Extract key financial metrics from text using regex patterns"""
        metrics = {
            'revenue': None,
            'gross_margin': None,
            'net_income': None,
            'ebitda': None,
            'eps': None
        }
        
        # Regular expressions for common financial metrics
        patterns = {
            'revenue': r'revenue.*?\$?\s*([\d,]+\.?\d*)\s*million',
            'gross_margin': r'gross margin.*?([\d.]+)%',
            'net_income': r'net (income|loss).*?\$?\s*([-\d,]+\.?\d*)\s*million',
            'ebitda': r'ebitda.*?\$?\s*([\d,]+\.?\d*)\s*million',
            'eps': r'earnings per share.*?\$?\s*([-\d.]+)'
        }
        
        for metric, pattern in patterns.items():
            match = re.search(pattern, text.lower())
            if match:
                value = match.group(1)
                try:
                    metrics[metric] = float(value.replace(',', ''))
                except ValueError:
                    continue
                    
        return metrics
    
    def generate_comparative_analysis(self) -> Dict:
        """Generate comparative analysis of all processed reports"""
        comparison = {
            'companies': list(self.reports_data.keys()),
            'metrics': {}
        }
        
        for metric in ['revenue', 'gross_margin', 'net_income', 'ebitda', 'eps']:
            comparison['metrics'][metric] = {
                company: data['metrics'][metric]
                for company, data in self.reports_data.items()
                if data['metrics'][metric] is not None
            }
            
        return comparison

# FastAPI app
app = FastAPI()
analyzer = FinancialReportAnalyzer()

@app.post("/analyze-reports")
async def analyze_reports(reports: List[Dict[str, str]]):
    """
    Process multiple financial reports from different URLs
    reports: List of dicts containing company_name and url
    """
    results = []
    for report in reports:
        result = await analyzer.fetch_pdf(report['url'], report['company_name'])
        results.append(result)
    
    comparative_analysis = analyzer.generate_comparative_analysis()
    return {
        "results": results,
        "comparative_analysis": comparative_analysis
    }