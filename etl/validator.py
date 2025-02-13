# etl/validator.py
from .models import FinancialMetrics
from .logger import setup_logger

logger = setup_logger()

class DataValidator:
    def validate_data(self, data: dict) -> dict:
        try:
            metrics = FinancialMetrics(**data)
            return metrics.model_dump()  # Using model_dump instead of dict
        except Exception as e:
            logger.error(f"Data validation error: {str(e)}")
            raise