from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import URL
from datetime import datetime, timezone
from contextlib import contextmanager
from psycopg2 import connect, sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

class BaseMixin:
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

Base = declarative_base(cls=BaseMixin)

class Company(Base):
    __tablename__ = 'companies'
    rank = Column(Integer)
    name = Column(String(255), unique=True, nullable=False)
    website = Column(String(255))
    revenue = Column(Float)
    financials = relationship("Financial", back_populates="company")

class Financial(Base):
    __tablename__ = 'financials'
    company_id = Column(Integer, ForeignKey('companies.id'))
    revenue = Column(Float)
    net_income = Column(Float)
    operating_income = Column(Float)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    source = Column(String(50))
    data_date = Column(DateTime, nullable=False)
    raw_data = Column(JSONB)
    company = relationship("Company", back_populates="financials")

class DatabaseManager:
    def __init__(self):
        self.Session = None
        self.setup_database()

    def setup_database(self):
        db_params = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }

        self.ensure_database_exists(db_params)

        db_url = URL.create(
            drivername="postgresql",
            username=db_params['user'],
            password=db_params['password'],
            host=db_params['host'],
            port=db_params['port'],
            database=db_params['database']
        )

        self.engine = create_engine(db_url, echo=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def ensure_database_exists(self, db_params):
        try:
            # Connect to the default `postgres` database
            connection = connect(
                dbname="postgres",
                user=db_params['user'],
                password=db_params['password'],
                host=db_params['host'],
                port=db_params['port']
            )
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = connection.cursor()

            # Check if the database exists
            cursor.execute(
                sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"),
                [db_params['database']]
            )
            exists = cursor.fetchone()

            if not exists:
                # Create the database if it doesn't exist
                cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(db_params['database'])
                    )
                )
                logging.info(f"Database '{db_params['database']}' created successfully.")
            else:
                logging.info(f"Database '{db_params['database']}' already exists.")

            cursor.close()
            connection.close()

        except Exception as e:
            logging.error(f"Error ensuring database exists: {e}")
            raise

    @contextmanager
    def session_scope(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_company_data(self, company_data: dict):
        if not company_data or 'name' not in company_data:
            raise ValueError("Invalid company data: 'name' field is required.")

        with self.session_scope() as session:
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

            if 'metrics' in company_data:
                financial = Financial(
                    company_id=company.id,
                    revenue=company_data['metrics'].get('revenue'),
                    net_income=company_data['metrics'].get('net_income'),
                    operating_income=company_data['metrics'].get('operating_income'),
                    total_assets=company_data['metrics'].get('total_assets'),
                    total_liabilities=company_data['metrics'].get('total_liabilities'),
                    source=company_data.get('source', 'web'),
                    data_date=datetime.now(timezone.utc),
                    raw_data=company_data
                )
                session.add(financial)
