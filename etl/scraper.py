# etl/scraper.py
import requests
import json
import time
from datetime import datetime, timezone
from .logger import setup_logger

logger = setup_logger()

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
