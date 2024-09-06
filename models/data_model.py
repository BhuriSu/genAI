# models/data_model.py
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class CsvRecord(Base):
    """
    Defines a table for CSV data in a database.
    """
    __tablename__ = 'csv_data'

    id = Column(Integer, primary_key=True, index=True)
    column_1 = Column(String)
    column_2 = Column(String)
    column_3 = Column(Float)

    def __repr__(self):
        return f"<CsvRecord(column_1={self.column_1}, column_2={self.column_2}, column_3={self.column_3})>"

# Create an in-memory SQLite database for simplicity
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
