import pytest
from unittest.mock import patch, MagicMock
import asyncio
from scrape.scrape import Fortune500Scraper
import os

@pytest.fixture
def scraper():
    """Fixture to initialize the Fortune500Scraper."""
    return Fortune500Scraper(output_dir="test_data")


def test_setup_directories(scraper):
    """Test if necessary directories are created."""
    scraper.setup_directories()
    directories = [
        scraper.output_dir,
        f"{scraper.output_dir}/pdfs",
        f"{scraper.output_dir}/raw_data",
        f"{scraper.output_dir}/processed_data",
    ]
    for directory in directories:
        assert os.path.exists(directory), f"{directory} does not exist"


@patch("aiohttp.ClientSession.get")
@pytest.mark.asyncio
async def test_fetch_fortune_500_list(mock_get, scraper):
    """Test fetching the Fortune 500 list."""
    # Mock response
    html = """
    <div class="company-list-item">
        <div class="rank">1</div>
        <div class="company-name">Company A</div>
        <div class="revenue">$100 Billion</div>
        <a class="website-link" href="http://example.com">Website</a>
    </div>
    """
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = asyncio.Future()
    mock_response.text.set_result(html)
    mock_get.return_value = mock_response

    companies = await scraper.fetch_fortune_500_list()
    assert len(companies) == 1
    assert companies[0]["name"] == "Company A"
    assert companies[0]["revenue"] == "$100 Billion"


@patch("aiohttp.ClientSession.get")
@pytest.mark.asyncio
async def test_extract_pdf_financials(mock_get, scraper):
    """Test extracting financial data from a PDF."""
    pdf_content = b"%PDF-1.4...mock pdf content"
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read = asyncio.Future()
    mock_response.read.set_result(pdf_content)
    mock_get.return_value = mock_response

    metrics = await scraper.extract_pdf_financials(
        "http://example.com/report.pdf", "Test Company"
    )
    # Test if metrics is a dictionary
    assert isinstance(metrics, dict)


@patch("selenium.webdriver.Chrome")
def test_scrape_company_website(mock_chrome, scraper):
    """Test scraping company website."""
    # Mock the WebDriver
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    mock_driver.find_elements.return_value = [
        MagicMock(get_attribute=lambda attr: "http://example.com/sample.pdf")
    ]

    financials = asyncio.run(scraper.scrape_company_website("http://example.com", "Test Company"))
    assert "quarterly_reports" in financials
    assert len(financials["quarterly_reports"]) > 0


@patch("aiohttp.ClientSession.get")
@pytest.mark.asyncio
async def test_fetch_sec_filings(mock_get, scraper):
    """Test fetching SEC filings."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = asyncio.Future()
    mock_response.json.set_result({"filings": [{"title": "10-K"}]})
    mock_get.return_value = mock_response

    filings = await scraper.fetch_sec_filings("Test Company")
    assert len(filings) == 1
    assert filings[0]["title"] == "10-K"


def test_calculate_financial_ratios(scraper):
    """Test financial ratio calculation."""
    metrics = {
        "net_income": 5000,
        "revenue": 20000,
        "total_assets": 50000,
        "total_liabilities": 30000,
    }
    ratios = scraper.calculate_financial_ratios(metrics)
    assert "profit_margin" in ratios
    assert ratios["profit_margin"] == 0.25
    assert "debt_to_assets" in ratios
    assert ratios["debt_to_assets"] == 0.6
