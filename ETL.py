import pandas as pd
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import logging
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# Construct database URL
def get_database_url():
    return f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Database setup
Base = declarative_base()

class FinancialReport(Base):
    __tablename__ = 'financial_reports'
    
    id = Column(Integer, primary_key=True)
    company_name = Column(String)
    report_date = Column(DateTime)
    revenue = Column(Float)
    net_income = Column(Float)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    operating_cash_flow = Column(Float)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

# Web Scraping Component
class FinancialScraper:
    def __init__(self, companies):
        self.companies = companies
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_company(self, company):
        try:
            # This is a placeholder for the actual scraping logic
            # You would need to implement specific scraping rules for each source
            url = f"https://example.com/financials/{company}"
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract financial data (implement based on actual HTML structure)
            data = {
                'company_name': company,
                'report_date': datetime.now(),  # Replace with actual report date
                'revenue': self._extract_value(soup, 'revenue'),
                'net_income': self._extract_value(soup, 'net_income'),
                'total_assets': self._extract_value(soup, 'total_assets'),
                'total_liabilities': self._extract_value(soup, 'total_liabilities'),
                'operating_cash_flow': self._extract_value(soup, 'operating_cash_flow')
            }
            return data
        except Exception as e:
            logger.error(f"Error scraping {company}: {str(e)}")
            return None
    
    def _extract_value(self, soup, field):
        # Implement specific extraction logic based on the website structure
        return 0.0  # Placeholder
    
    def scrape_all(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(self.scrape_company, self.companies))
        return [r for r in results if r is not None]

# ETL Component
class FinancialETL:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def transform_data(self, raw_data):
        df = pd.DataFrame(raw_data)
        
        # Basic data cleaning
        df = df.replace([np.inf, -np.inf], np.nan)
        
        # Calculate financial ratios
        df['current_ratio'] = df['total_assets'] / df['total_liabilities']
        df['profit_margin'] = df['net_income'] / df['revenue']
        
        return df
    
    def load_data(self, transformed_data):
        session = self.Session()
        try:
            for _, row in transformed_data.iterrows():
                report = FinancialReport(**row.to_dict())
                session.add(report)
            session.commit()
            logger.info("Data successfully loaded to database")
        except Exception as e:
            session.rollback()
            logger.error(f"Error loading data: {str(e)}")
        finally:
            session.close()

# ML Data Preparation Component
class MLDataPreparator:
    def __init__(self):
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy='mean')
    
    def prepare_data(self, df):
        # Select features for ML
        feature_columns = [
            'revenue', 'net_income', 'total_assets',
            'total_liabilities', 'operating_cash_flow',
            'current_ratio', 'profit_margin'
        ]
        
        # Handle missing values
        X = self.imputer.fit_transform(df[feature_columns])
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        return pd.DataFrame(
            X_scaled,
            columns=feature_columns,
            index=df.index
        )

# Main Pipeline
def run_pipeline(companies):
    # Initialize components with secure database connection
    db_url = get_database_url()
    
    # Validate database configuration
    if not all(DB_CONFIG.values()):
        raise ValueError("Missing required database configuration. Please check your .env file.")
    
    scraper = FinancialScraper(companies)
    etl = FinancialETL(db_url)
    ml_prep = MLDataPreparator()
    
    # Execute pipeline
    logger.info("Starting data collection...")
    raw_data = scraper.scrape_all()
    
    logger.info("Transforming data...")
    transformed_data = etl.transform_data(raw_data)
    
    logger.info("Loading data to database...")
    etl.load_data(transformed_data)
    
    logger.info("Preparing data for ML...")
    ml_ready_data = ml_prep.prepare_data(transformed_data)
    
    return ml_ready_data

# Example usage
if __name__ == "__main__":
    companies = [
        "company1",
        "company2",
        # Add more companies
    ]
    
    try:
        ml_ready_data = run_pipeline(companies)
        print("Pipeline completed successfully")
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")