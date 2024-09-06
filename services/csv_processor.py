from services.utils import validate_file_extension, parse_csv

class CsvProcessor:
    def __init__(self):
        self.data = None

    async def process_csv(self, file):
        validate_file_extension(file.filename)  # Ensure file is CSV
        contents = await file.read()
        self.data = parse_csv(contents)  # Parse CSV using utility function
        return self.data

    def get_data(self):
        return self.data

    def is_csv_loaded(self):
        return self.data is not None

    def query_data(self, sql_query):
        try:
            result = self.data.query(sql_query)
            return result.to_dict(orient='records')
        except Exception as e:
            return {"error": str(e)}
