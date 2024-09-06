import os
from fastapi import HTTPException
import pandas as pd

def validate_file_extension(file_name: str):
    """
    Validates if the uploaded file is a CSV.
    """
    ext = os.path.splitext(file_name)[1]
    if ext != '.csv':
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

def parse_csv(content: bytes) -> pd.DataFrame:
    """
    Parse the uploaded CSV file content into a Pandas DataFrame.
    """
    try:
        df = pd.read_csv(pd.compat.StringIO(content.decode("utf-8")))
        return df
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")