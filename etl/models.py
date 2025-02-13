# etl/models.py
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
from pydantic import BaseModel, field_validator
from typing import Optional
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class FinancialMetrics(BaseModel):
    revenue: Optional[float]
    net_income: Optional[float]
    total_assets: Optional[float]
    total_liabilities: Optional[float]
    operating_cash_flow: Optional[float]
    
    @field_validator('revenue', 'net_income', 'total_assets', 'total_liabilities', 'operating_cash_flow')
    @classmethod
    def validate_metrics(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v > 1e12 or v < -1e12):
            raise ValueError(f"Metric value {v} seems unrealistic")
        return v

class FinancialReport(Base):
    __tablename__ = 'financial_reports'
    id = Column(Integer, primary_key=True)
    cik = Column(String)
    company_name = Column(String)
    filing_type = Column(String)
    filing_date = Column(DateTime)
    fiscal_year = Column(Integer)
    fiscal_period = Column(String)
    revenue = Column(Float)
    net_income = Column(Float)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    operating_cash_flow = Column(Float)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    text_content = Column(String)
    embeddings = Column(Vector(384))