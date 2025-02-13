# etl/text_processor.py
from sentence_transformers import SentenceTransformer

class TextProcessor:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def process_financial_data(self, data):
        text = self._generate_text(data)
        embeddings = self.embedding_model.encode(text)
        return text, embeddings
    
    def _generate_text(self, data):
        text = f"""
        Financial Report for {data['company_name']} (CIK: {data['cik']})
        Filing Date: {data['filing_date']}
        Fiscal Year: {data['fiscal_year']}
        
        Key Financial Metrics:
        - Revenue: ${data['revenue']:,.2f}
        - Net Income: ${data['net_income']:,.2f}
        - Total Assets: ${data['total_assets']:,.2f}
        - Total Liabilities: ${data['total_liabilities']:,.2f}
        - Operating Cash Flow: ${data['operating_cash_flow']:,.2f}
        """
        return text