import pytest
from datetime import datetime, timezone
from database.database import DatabaseManager, Company, Financial  # Adjusted import
from sqlalchemy import text

@pytest.fixture(scope="module")
def test_db():
    """Set up a testing database."""
    db_manager = DatabaseManager()
    return db_manager

def test_database_connection(test_db):
    """Test if the database connection works."""
    try:
        session = test_db.Session()
        session.execute(text("SELECT 1"))  # Wrap the raw SQL string with `text`
        session.close()
    except Exception as e:
        pytest.fail(f"Database connection test failed: {e}")

def test_create_company(test_db):
    """Test creating a company in the database."""
    session = test_db.Session()
    company = Company(
        name="Test Company",
        rank=1,
        website="https://testcompany.com",
        revenue=12345.67,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    session.add(company)
    session.commit()

    # Verify company exists
    saved_company = session.query(Company).filter_by(name="Test Company").first()
    assert saved_company is not None
    assert saved_company.name == "Test Company"
    assert saved_company.rank == 1
    session.close()

def test_create_financial(test_db):
    """Test adding financial data for a company."""
    session = test_db.Session()
    company = session.query(Company).filter_by(name="Test Company").first()
    assert company is not None

    financial = Financial(
        company_id=company.id,
        revenue=12345.67,
        net_income=2345.67,
        operating_income=345.67,
        total_assets=45678.90,
        total_liabilities=12345.67,
        source="test",
        data_date=datetime.now(timezone.utc),
        raw_data={"test": "data"},
        created_at=datetime.now(timezone.utc)
    )
    session.add(financial)
    session.commit()

    # Verify financial exists
    saved_financial = session.query(Financial).filter_by(company_id=company.id).first()
    assert saved_financial is not None
    assert saved_financial.revenue == 12345.67
    session.close()

def test_cleanup(test_db):
    """Clean up test data from the database."""
    session = test_db.Session()
    session.query(Financial).delete()
    session.query(Company).delete()
    session.commit()
    session.close()
