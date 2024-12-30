from playwright.sync_api import sync_playwright
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class RAGSystem:
    def __init__(self):
        self.client = QdrantClient(host="localhost", port=6333)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
    def scrape_content(self, url):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            content = page.content()
            browser.close()
        return content

    def process_content(self, content, collection_name="web_content"):
        # Process and store content in Qdrant
        embedding = self.encoder.encode([content])[0]
        self.client.upsert(
            collection_name=collection_name,
            points=[(1, embedding, {"text": content})]
        )

    def query(self, question):
        # Query similar content
        query_vector = self.encoder.encode([question])[0]
        return self.client.search(
            collection_name="web_content",
            query_vector=query_vector,
            limit=5
        )