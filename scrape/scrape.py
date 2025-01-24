from typing import Dict, List, Optional
import requests
import io
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import os
from datetime import datetime
import json
import fitz  # PyMuPDF for better PDF handling
from fake_useragent import UserAgent
import aiohttp
import asyncio
from database.database import DatabaseManager

class Fortune500Scraper:
    def __init__(self, output_dir: str = "financial_data"):
        """Initialize the scraper with configuration and logging."""
        self.db = DatabaseManager()
        self.output_dir = output_dir
        self.session = requests.Session()
        self.ua = UserAgent()
        self.companies_data = {}
        self.setup_logging()
        self.setup_directories()
        
        # Configure Chrome options for Selenium
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Rate limiting configuration
        self.rate_limit = 1  # seconds between requests
        self.last_request_time = 0
        
        # Load API keys and configs from environment variables
        self.sec_api_key = os.getenv('SEC_API_KEY')
        self.proxy_list = self.load_proxy_list()

    def setup_logging(self):
        """Configure logging for the scraper."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'scraper_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_directories(self):
        """Create necessary directories for data storage."""
        directories = [
            self.output_dir,
            f"{self.output_dir}/pdfs",
            f"{self.output_dir}/raw_data",
            f"{self.output_dir}/processed_data"
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def load_proxy_list(self) -> List[str]:
        """Load list of proxy servers from configuration."""
        try:
            with open('proxy_list.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    async def fetch_fortune_500_list(self) -> List[Dict]:
        """Fetch the current Fortune 500 company list."""
        url = "https://fortune.com/fortune500/"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'User-Agent': self.ua.random}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    companies = []
                    
                    # Extract company data (adjust selectors based on Fortune's website structure)
                    for company in soup.select('.company-list-item'):
                        companies.append({
                            'rank': company.select_one('.rank').text.strip(),
                            'name': company.select_one('.company-name').text.strip(),
                            'revenue': company.select_one('.revenue').text.strip(),
                            'website': company.select_one('.website-link')['href']
                        })
                    
                    return companies
        return []

    async def extract_pdf_financials(self, pdf_url: str, company_name: str) -> Dict:
        """Extract financial data from PDF reports."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(pdf_url) as response:
                    if response.status == 200:
                        pdf_content = await response.read()
                        pdf_file = io.BytesIO(pdf_content)
                        
                        # Use PyMuPDF for better PDF parsing
                        doc = fitz.open(stream=pdf_file, filetype="pdf")
                        text = ""
                        for page in doc:
                            text += page.get_text()
                        
                        # Extract financial metrics using regex patterns
                        metrics = {
                            'revenue': self.extract_metric(text, r'Revenue.*?\$?([\d,]+(?:\.\d+)?)\s*(?:billion|million)?'),
                            'net_income': self.extract_metric(text, r'Net Income.*?\$?([\d,]+(?:\.\d+)?)\s*(?:billion|million)?'),
                            'operating_income': self.extract_metric(text, r'Operating Income.*?\$?([\d,]+(?:\.\d+)?)\s*(?:billion|million)?'),
                            'total_assets': self.extract_metric(text, r'Total Assets.*?\$?([\d,]+(?:\.\d+)?)\s*(?:billion|million)?'),
                            'total_liabilities': self.extract_metric(text, r'Total Liabilities.*?\$?([\d,]+(?:\.\d+)?)\s*(?:billion|million)?')
                        }
                        
                        # Save raw PDF for reference
                        pdf_path = f"{self.output_dir}/pdfs/{company_name.replace(' ', '_')}_report.pdf"
                        with open(pdf_path, 'wb') as f:
                            f.write(pdf_content)
                        
                        return metrics
                        
        except Exception as e:
            self.logger.error(f"Error extracting PDF data for {company_name}: {str(e)}")
            return {}

    def extract_metric(self, text: str, pattern: str) -> Optional[float]:
        """Extract and normalize financial metrics from text."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(',', '')
            if 'billion' in text.lower():
                return float(value) * 1000
            elif 'million' in text.lower():
                return float(value)
        return None

    async def scrape_company_website(self, url: str, company_name: str) -> Dict:
        """Scrape financial data from company website."""
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            wait = WebDriverWait(driver, 10)
            
            driver.get(url)
            
            # Wait for investor relations or financial data section
            investor_link = wait.until(EC.presence_of_element_located((
                By.XPATH, 
                "//*[contains(text(), 'Investor') or contains(text(), 'Financial')]"
            )))
            investor_link.click()
            
            # Extract financial data
            financials = {
                'quarterly_reports': [],
                'annual_reports': [],
                'presentations': [],
                'sec_filings': []
            }
            
            # Look for financial documents and links
            links = driver.find_elements(By.TAG_NAME, 'a')
            for link in links:
                href = link.get_attribute('href')
                text = link.text.lower()
                
                if href and href.endswith('.pdf'):
                    if 'quarter' in text:
                        financials['quarterly_reports'].append(href)
                    elif 'annual' in text:
                        financials['annual_reports'].append(href)
                    elif 'presentation' in text:
                        financials['presentations'].append(href)
                
            # Save raw data
            with open(f"{self.output_dir}/raw_data/{company_name.replace(' ', '_')}_web.json", 'w') as f:
                json.dump(financials, f, indent=4)
            
            return financials
            
        except Exception as e:
            self.logger.error(f"Error scraping website for {company_name}: {str(e)}")
            return {}
        finally:
            if 'driver' in locals():
                driver.quit()

    async def fetch_sec_filings(self, company_name: str) -> List[Dict]:
        """Fetch SEC filings using SEC API."""
        if not self.sec_api_key:
            return []
            
        try:
            url = f"https://api.sec-api.io/companies/{company_name}/filings"
            headers = {'Authorization': f'Bearer {self.sec_api_key}'}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('filings', [])
                        
        except Exception as e:
            self.logger.error(f"Error fetching SEC filings for {company_name}: {str(e)}")
            return []

    def process_financial_data(self, company_data: Dict) -> Dict:
        """Process and normalize financial data from different sources."""
        processed_data = {
            'company_name': company_data.get('name'),
            'metrics': {},
            'reports': {},
            'trends': {}
        }
        
        # Combine and normalize metrics
        if 'pdf_data' in company_data:
            processed_data['metrics'].update(company_data['pdf_data'])
        
        if 'web_data' in company_data:
            # Process web scraped data
            web_metrics = self.extract_web_metrics(company_data['web_data'])
            processed_data['metrics'].update(web_metrics)
        
        # Calculate financial ratios
        processed_data['ratios'] = self.calculate_financial_ratios(processed_data['metrics'])
        
        return processed_data

    def calculate_financial_ratios(self, metrics: Dict) -> Dict:
        """Calculate key financial ratios from metrics."""
        ratios = {}
        
        if 'net_income' in metrics and 'revenue' in metrics:
            ratios['profit_margin'] = metrics['net_income'] / metrics['revenue']
            
        if 'total_assets' in metrics and 'total_liabilities' in metrics:
            ratios['debt_to_assets'] = metrics['total_liabilities'] / metrics['total_assets']
            
        return ratios

    async def run_scraper(self):
        """Main method to run the scraper."""
        try:
            # Fetch Fortune 500 list
            companies = await self.fetch_fortune_500_list()
            self.logger.info(f"Found {len(companies)} companies")
            
            # Process each company
            for company in companies:
                self.logger.info(f"Processing {company['name']}")
                
                # Fetch data from multiple sources concurrently
                tasks = [
                    self.scrape_company_website(company['website'], company['name']),
                    self.fetch_sec_filings(company['name'])
                ]
                
                # If PDF URL is available
                if 'annual_report_url' in company:
                    tasks.append(self.extract_pdf_financials(company['annual_report_url'], company['name']))
                
                results = await asyncio.gather(*tasks)
                
                # Combine results
                company_data = {
                    'web_data': results[0],
                    'sec_filings': results[1],
                    'pdf_data': results[2] if len(results) > 2 else {}
                }
                
                # Process and save data
                processed_data = self.process_financial_data(company_data)
    
                try:
                    self.db.save_company_data(processed_data)
                    self.logger.info(f"Saved data for {company['name']} to database")
                except Exception as e:
                    self.logger.error(f"Error saving {company['name']} to database: {str(e)}")
                
                output_file = f"{self.output_dir}/processed_data/{company['name'].replace(' ', '_')}.json"
                with open(output_file, 'w') as f:
                    json.dump(processed_data, f, indent=4)
                
                # Rate limiting
                await asyncio.sleep(self.rate_limit)
                
        except Exception as e:
            self.logger.error(f"Error in scraper: {str(e)}")
            raise

class DatabaseManager:
    def __init__(self):
        pass
    
    def save_company_data(self, data):
        print(f"Saving data: {data}")