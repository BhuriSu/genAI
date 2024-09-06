from fastapi import FastAPI, File, UploadFile, HTTPException
from services.csv_processor import CsvProcessor
from services.gpt_query import GPTQueryProcessor

app = FastAPI()
csv_processor = CsvProcessor()
gpt_processor = GPTQueryProcessor()

@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    if file.filename.endswith('.csv'):
        data = await csv_processor.process_csv(file)
        return {"message": "CSV uploaded successfully", "columns": data.columns.tolist()}
    else:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

@app.post("/ask/")
async def ask_question(question: str):
    if not csv_processor.is_csv_loaded():
        raise HTTPException(status_code=400, detail="CSV file not loaded. Upload a CSV first.")
    
    csv_data = csv_processor.get_data()
    query = gpt_processor.convert_to_sql(question, csv_data)
    result = csv_processor.query_data(query)
    return {"result": result}
