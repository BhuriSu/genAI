
import pandas as pd
from playwright.sync_api import sync_playwright
import agentql
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def scrape_companies_data(num_pages=1):
    """
    Scrape company market cap data using AgentQL
    """
    companies_data = []
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Wrap the page with AgentQL
        agent_page = agentql.wrap(page)
        
        for page_num in range(num_pages):
            url = f"https://companiesmarketcap.com/page/{page_num + 1}/"
            print(f"\nAccessing page {page_num + 1}...")
            
            # Navigate to the page
            agent_page.goto(url)
            
            # Wait for table to be visible and loaded
            print("Waiting for content to load...")
            agent_page.wait_for_selector('.companies-list')
            
            # Execute JavaScript to extract data
            print("Extracting data...")
            companies = page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('tr.company-row');
                    return Array.from(rows).map(row => ({
                        name: row.querySelector('.company-name')?.textContent?.trim() || '',
                        symbol: row.querySelector('.company-code')?.textContent?.trim() || '',
                        market_cap: row.querySelector('td:nth-child(3)')?.textContent?.trim() || '',
                        price: row.querySelector('td:nth-child(4)')?.textContent?.trim() || '',
                        change_24h: row.querySelector('td:nth-child(5)')?.textContent?.trim() || ''
                    }));
                }
            """)
            
            # Process extracted data
            for company in companies:
                try:
                    company['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    companies_data.append(company)
                    print(f"Scraped: {company['name']} ({company['symbol']})")
                except Exception as e:
                    print(f"Error processing company: {e}")
                    continue
            
            # Wait between pages
            print("Waiting before next page...")
            agent_page.wait_for_timeout(3000)
        
        print("\nClosing browser...")
        browser.close()
    
    return companies_data

def save_to_csv(data, filename='companies_market_cap.csv'):
    """
    Save scraped data to CSV file
    """
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def main():
    try:
        print("Starting scraping process...")
        companies_data = scrape_companies_data(num_pages=3)
        
        if companies_data:
            save_to_csv(companies_data)
            print(f"\nSuccessfully scraped {len(companies_data)} companies")
        else:
            print("No data was scraped")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()