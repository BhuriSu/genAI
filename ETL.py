import pandas as pd
import requests
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
import logging
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
            'User-Agent': 'aozro shonuvy@email.com',  # Replace with your details
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
            
            # Get the list of all companies
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

    def format_accession(self, accession):
        """Format accession number by removing dashes"""
        return accession.replace('-', '') if accession else ''

    def get_filing_data(self, accession_number, cik):
        """Get filing data using the correct URL format"""
        try:
            # Format CIK and accession number
            cik = cik.lstrip('0')  # Remove leading zeros for URL
            
            # Add delay to comply with SEC EDGAR rate limits
            time.sleep(0.1)
            
            # Get the filing metadata
            metadata_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"
            logger.debug(f"Fetching metadata from: {metadata_url}")
            
            response = requests.get(metadata_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant financial data from the facts
                financial_data = {
                    'revenue': self.extract_fact(data, 'Revenues'),
                    'net_income': self.extract_fact(data, 'NetIncomeLoss'),
                    'total_assets': self.extract_fact(data, 'Assets'),
                    'total_liabilities': self.extract_fact(data, 'Liabilities'),
                    'operating_cash_flow': self.extract_fact(data, 'NetCashProvidedByUsedInOperatingActivities')
                }
                
                return financial_data
            else:
                logger.warning(f"Failed to fetch data for CIK {cik}. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting filing data for CIK {cik}: {str(e)}")
            return None

    def extract_fact(self, data, concept):
        """Extract the most recent value for a given concept"""
        try:
            if 'facts' not in data:
                return None
                
            us_gaap = data['facts'].get('us-gaap', {})
            concept_data = us_gaap.get(concept, None)
            
            if not concept_data or 'units' not in concept_data:
                return None
            
            # Get the first available unit (usually USD)
            first_unit = next(iter(concept_data['units'].values()))
            
            # Sort by period end date to get the most recent value
            sorted_facts = sorted(
                first_unit,
                key=lambda x: x.get('end', ''),
                reverse=True
            )
            
            if sorted_facts:
                return float(sorted_facts[0]['val'])
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting {concept}: {str(e)}")
            return None

    def scrape_company(self, cik):
        """Scrape latest financial data for a company"""
        try:
            # Get company facts directly
            financial_data = self.get_filing_data(None, cik)
            
            if not financial_data:
                return None

            # Get company name
            company_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            response = requests.get(company_url, headers=self.headers)
            
            if response.status_code == 200:
                company_data = response.json()
                company_name = company_data.get('name', 'Unknown')
            else:
                company_name = f"Company {cik}"

            return {
                'cik': cik,
                'company_name': company_name,
                'filing_type': '10-K',
                'filing_date': datetime.now(timezone.utc),
                'fiscal_year': datetime.now().year,
                'fiscal_period': 'FY',
                **financial_data
            }

        except Exception as e:
            logger.error(f"Error scraping CIK {cik}: {str(e)}")
            return None

    def scrape_all(self):
        """Scrape data for all companies"""
        ciks = self.get_fortune500_ciks()
        results = []
        
        for cik in ciks:
            try:
                # Add delay between companies
                time.sleep(0.1)
                result = self.scrape_company(cik)
                if result:
                    results.append(result)
                    logger.info(f"Successfully scraped data for {result['company_name']}")
            except Exception as e:
                logger.error(f"Error processing CIK {cik}: {str(e)}")
                continue
        
        logger.info(f"Successfully scraped data for {len(results)} companies")
        return results

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