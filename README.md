### Data Engineering System Project for asking through csv with advanced prompt management

1.Upload csv file 
2.Ask about information inside that csv file using OpenAI API for language model queries, 
LangChain for advanced prompt management and SQLAlchemy for handling database interactions. 
3.Generate answer to user 

### How to run 
1.docker build -t csv-nlp-query .
2.docker run -p 8000:8000 csv-nlp-query
3.Once the container is running, you can access the FastAPI service at: http://localhost:8000