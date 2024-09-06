# **Data Engineering System Project: Query CSV with Natural Language**

This project allows users to upload a CSV file and ask questions about the data inside using natural language. It leverages the **OpenAI API** for language model queries, **LangChain** for advanced prompt management, and **SQLAlchemy** for handling optional database interactions.

## **Features**
1. **CSV Upload**: Upload a CSV file via a FastAPI-powered web interface.
2. **Natural Language Queries**: Ask questions about the CSV file contents in natural language.
3. **Advanced Prompt Management**: LangChain is used to manage and structure prompts to interact with the OpenAI API.
4. **SQL-like Queries**: Queries about the CSV data are interpreted as if querying a database, returning structured responses.
5. **Optional Database Support**: SQLAlchemy can be used to store and manage CSV data in a relational database (e.g., SQLite or PostgreSQL).

---

## **Getting Started**

### **Prerequisites**
- Docker installed on your system.
- OpenAI API key (You’ll need to set this up as an environment variable for the service to communicate with OpenAI’s language model).

---

### **How to Run the Project**

1. **Clone the Repository**
   ```
   git clone https://github.com/your-repo/csv-nlp-query.git
   cd csv-nlp-query
   ```

2. **Set Up Environment Variables**
   ```
   OPENAI_API_KEY=your_openai_api_key
   DATABASE_URL=sqlite:///./test.db 
   ```
3. **Build the Docker Image And Run the Docker Container**
   ```
   docker build -t csv-nlp-query .
   docker run -p 8000:8000 csv-nlp-query
   ```
4. **Once the container is running, you can access the FastAPI application at: http://localhost:8000**

## **Technologies Used**

- **FastAPI**: For building the RESTful API.
- **OpenAI API**: For natural language processing and answering questions.
- **LangChain**: For prompt management and advanced NLP capabilities.
- **Pandas**: For CSV parsing and data manipulation.
- **SQLAlchemy**: Optional, for storing and querying CSV data in a database.
- **Docker**: For containerizing the application.