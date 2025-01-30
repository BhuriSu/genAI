import pandas as pd
import requests
import xml.etree.ElementTree as ET
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
import logging
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import os
from dotenv import load_dotenv
import time
import json

# Load environment variables
load_dotenv()
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    # cik number is used on the SEC's computer systems to identify corporations and individual people who have filed disclosure with the SEC.
    id = Column(Integer, primary_key=True)
    cik = Column(String)  
    company_name = Column(String)
    filing_type = Column(String)  # Added filing type (10-K, 10-Q)
    filing_date = Column(DateTime)
    fiscal_year = Column(Integer)
    fiscal_period = Column(String)
    revenue = Column(Float)
    net_income = Column(Float)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    operating_cash_flow = Column(Float)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

# Web Scraping Component
class SECEdgarScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'azoro shonuvy@email.com',  # Replace with your details
            'Accept-Encoding': 'gzip, deflate'
        }
        self.base_url = "https://www.sec.gov/files/company_tickers.json"
    
    def get_fortune500_ciks(self):
        """Get CIK numbers for Fortune 500 companies"""
        try:
            logger.info("Fetching company CIKs from SEC EDGAR...")
            
            # Use requests Session for better performance
            session = requests.Session()
            session.headers.update(self.headers)
            
            # First, get the list of all companies
            response = session.get(self.base_url)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch CIKs. Status code: {response.status_code}")
                logger.error(f"Response content: {response.text[:200]}...")
                raise requests.exceptions.RequestException(
                    f"Failed to fetch CIKs. Status code: {response.status_code}"
                )
            
            # Parse the JSON response
            companies_data = response.json()
            
            # Sort companies by market cap or another metric if available
            companies_list = []
            for _, company in companies_data.items():
                companies_list.append({
                    'cik_str': str(company['cik_str']).zfill(10),
                    'ticker': company['ticker'],
                    'title': company['title']
                })
            
            # Take the first 500 companies
            ciks = [company['cik_str'] for company in companies_list[:500]]
            
            logger.info(f"Successfully retrieved {len(ciks)} CIKs")
            
            # Log some sample companies for verification
            for i in range(min(5, len(companies_list))):
                logger.info(f"Sample company {i+1}: {companies_list[i]['title']} (CIK: {companies_list[i]['cik_str']})")
            
            return ciks
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching CIKs: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Response content: {response.text[:200]}...")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching CIKs: {str(e)}")
            raise

    def get_company_submissions(self, cik):
        """Get company's filing history"""
        try:
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            
            # Add delay to comply with SEC EDGAR rate limits
            time.sleep(0.1)  # 100ms delay between requests
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch submissions for CIK {cik}. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching submissions for CIK {cik}: {str(e)}")
            return None

    def get_filing_data(self, accession_number, cik):
        """Get XBRL data from a specific filing"""
        try:
            # Add delay to comply with SEC EDGAR rate limits
            time.sleep(0.1)  # 100ms delay between requests
            
            # Get the filing's directory listing
            url = f"https://data.sec.gov/Archives/edgar/data/{int(cik)}/{accession_number}/index.json"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch filing data for CIK {cik}. Status code: {response.status_code}")
                return None

            # Find the XBRL file
            files = response.json()['directory']['item']
            xbrl_file = next((f for f in files if f['name'].endswith('.xml')), None)
            
            if not xbrl_file:
                logger.warning(f"No XBRL file found for CIK {cik}")
                return None

            # Get XBRL content
            xbrl_url = f"https://data.sec.gov/Archives/edgar/data/{int(cik)}/{accession_number}/{xbrl_file['name']}"
            response = requests.get(xbrl_url, headers=self.headers)
            
            return self._parse_xbrl(response.content)
            
        except Exception as e:
            logger.error(f"Error getting filing data for CIK {cik}: {str(e)}")
            return None

    def _parse_xbrl(self, content):
        """Parse XBRL content for financial metrics"""
        try:
            root = ET.fromstring(content)
            
            # Define XBRL tags mapping
            tags = {
                'revenue': [
                    './/us-gaap:Revenues',
                    './/us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
                ],
                'net_income': [
                    './/us-gaap:NetIncomeLoss',
                    './/us-gaap:ProfitLoss'
                ],
                'total_assets': [
                    './/us-gaap:Assets',
                    './/us-gaap:AssetsCurrent'
                ],
                'total_liabilities': [
                    './/us-gaap:Liabilities',
                    './/us-gaap:LiabilitiesCurrent'
                ],
                'operating_cash_flow': [
                    './/us-gaap:NetCashProvidedByUsedInOperatingActivities'
                ]
            }
            
            data = {}
            for metric, possible_tags in tags.items():
                for tag in possible_tags:
                    element = root.find(tag)
                    if element is not None:
                        try:
                            data[metric] = float(element.text)
                            break
                        except (ValueError, TypeError):
                            continue
                
                if metric not in data:
                    data[metric] = None
                    
            return data
        except Exception as e:
            logger.error(f"Error parsing XBRL: {str(e)}")
            return None

    def scrape_company(self, cik):
        """Scrape latest financial data for a company"""
        try:
            submissions = self.get_company_submissions(cik)
            if not submissions:
                return None

            # Get latest 10-K filing
            recent_filings = submissions.get('filings', {}).get('recent', {})
            if not recent_filings:
                return None

            # Find index of latest 10-K
            form_index = next((i for i, form in enumerate(recent_filings['form']) 
                             if form == '10-K'), None)
            if form_index is None:
                return None

            accession_number = recent_filings['accessionNumber'][form_index]
            filing_date = recent_filings['filingDate'][form_index]
            
            financial_data = self.get_filing_data(accession_number, cik)
            if not financial_data:
                return None

            return {
                'cik': cik,
                'company_name': submissions['name'],
                'filing_type': '10-K',
                'filing_date': datetime.strptime(filing_date, '%Y-%m-%d'),
                'fiscal_year': int(filing_date[:4]),
                'fiscal_period': 'FY',
                **financial_data
            }

        except Exception as e:
            logger.error(f"Error scraping CIK {cik}: {str(e)}")
            return None

    def scrape_all(self):
        """Scrape data for all Fortune 500 companies"""
        ciks = self.get_fortune500_ciks()
        with ThreadPoolExecutor(max_workers=3) as executor:  # Limited workers due to SEC rate limits
            results = list(executor.map(self.scrape_company, ciks))
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
def run_pipeline():
    try:
        # Initialize components
        db_url = get_database_url()
        
        if not all(DB_CONFIG.values()):
            raise ValueError("Missing database configuration")
        
        scraper = SECEdgarScraper()
        etl = FinancialETL(db_url)
        
        logger.info("Starting SEC EDGAR data collection...")
        raw_data = scraper.scrape_all()
        
        if not raw_data:
            raise ValueError("No data was collected from SEC EDGAR")
        
        logger.info(f"Collected data for {len(raw_data)} companies")
        
        logger.info("Transforming data...")
        transformed_data = etl.transform_data(raw_data)
        
        logger.info("Loading data to database...")
        etl.load_data(transformed_data)
        
        return transformed_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        transformed_data = run_pipeline()
        print("Pipeline completed successfully")
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")