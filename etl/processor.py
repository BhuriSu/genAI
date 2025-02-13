# etl/processor.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np
from .text_processor import TextProcessor
from .models import Base, FinancialReport
from .logger import setup_logger
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import os
import json
logger = setup_logger()

class FinancialETL:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.text_processor = TextProcessor()
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy='mean')
    def transform_data(self, raw_data):
        df = pd.DataFrame(raw_data)
        
        # Basic data cleaning
        df = df.replace([np.inf, -np.inf], np.nan)
        
        # Calculate financial ratios
        df['current_ratio'] = df['total_assets'] / df['total_liabilities']
        df['profit_margin'] = df['net_income'] / df['revenue']
        
        processed_data = []
        for _, row in df.iterrows():
            text, embeddings = self.text_processor.process_financial_data(row)
            processed_row = row.to_dict()
            processed_row['text_content'] = text
            processed_row['embeddings'] = embeddings
            processed_data.append(processed_row)
        
        return pd.DataFrame(processed_data)
    
    def load_data(self, transformed_data):
        session = self.Session()
        try:
            # Batch insert for better performance
            reports = []
            for _, row in transformed_data.iterrows():
                report = FinancialReport(**row)
                reports.append(report)
            
            session.bulk_save_objects(reports)
            session.commit()
            logger.info(f"Successfully loaded {len(reports)} reports to database")
        except Exception as e:
            session.rollback()
            logger.error(f"Error loading data: {str(e)}")
            raise
        finally:
            session.close()

    def export_training_data(self, output_dir: str):
        """Export processed data for model training"""
        session = self.Session()
        try:
            reports = session.query(FinancialReport).all()
            
            training_data = []
            for report in reports:
                # Prepare training examples for visualization generation
                training_example = {
                    "input": report.text_content,
                    "output": {
                        "type": "financial_report",
                        "metrics": {
                            "revenue": report.revenue,
                            "net_income": report.net_income,
                            "total_assets": report.total_assets,
                            "total_liabilities": report.total_liabilities,
                            "operating_cash_flow": report.operating_cash_flow,
                            "current_ratio": report.current_ratio,
                            "profit_margin": report.profit_margin
                        }
                    }
                }
                training_data.append(training_example)
            
            # Save training data
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, 'training_data.json'), 'w') as f:
                json.dump(training_data, f, indent=2)
            
            logger.info(f"Exported {len(training_data)} training examples")
            
        except Exception as e:
            logger.error(f"Error exporting training data: {str(e)}")
            raise
        finally:
            session.close()