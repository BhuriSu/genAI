from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import os

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    rank = Column(Integer)
    name = Column(String(255), unique=True)
    website = Column(String(255))
    revenue = Column(Float)
    created_at = Column(DateTime, default=datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(datetime.timezone.utc), onupdate=datetime.now(datetime.timezone.utc))
    
    financials = relationship("Financial", back_populates="company")

class Financial(Base):
    __tablename__ = 'financials'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'))
    revenue = Column(Float)
    net_income = Column(Float)
    operating_income = Column(Float)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    source = Column(String(50))  # 'pdf' or 'web'
    data_date = Column(DateTime)
    raw_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.now(datetime.timezone.utc))
    
    company = relationship("Company", back_populates="financials")

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.Session = None
        self.setup_database()

    def setup_database(self):
        """Set up database connection using environment variables."""
        db_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'fortune500_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
        
        db_url = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_company_data(self, company_data: dict):
        """Save company and financial data to database."""
        session = self.Session()
        try:
            # Create or update company
            company = session.query(Company).filter_by(name=company_data['name']).first()
            if not company:
                company = Company(
                    name=company_data['name'],
                    rank=company_data.get('rank'),
                    website=company_data.get('website'),
                    revenue=company_data.get('revenue')
                )
                session.add(company)
                session.flush()

            # Add financial data
            if 'metrics' in company_data:
                financial = Financial(
                    company_id=company.id,
                    revenue=company_data['metrics'].get('revenue'),
                    net_income=company_data['metrics'].get('net_income'),
                    operating_income=company_data['metrics'].get('operating_income'),
                    total_assets=company_data['metrics'].get('total_assets'),
                    total_liabilities=company_data['metrics'].get('total_liabilities'),
                    source=company_data.get('source', 'web'),
                    data_date=datetime.now(),
                    raw_data=company_data
                )
                session.add(financial)

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()