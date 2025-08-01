# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import asyncio
import duckdb
from typing import List, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv

from vectorstore import build_vectorstore
from redact import redact_sensitive

# Load environment variables
load_dotenv()

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

def get_spending_data_from_db() -> List[Dict[str, Any]]:
    """Fetch spending data from DuckDB database"""
    try:
        conn = duckdb.connect('spending_insights.db')
        
        # Get transactions data
        transactions = conn.execute("""
            SELECT date, merchant, category, amount, notes
            FROM transactions
            ORDER BY date DESC
        """).fetchall()
        
        # Convert to list of dictionaries
        spending_data = []
        for row in transactions:
            spending_data.append({
                "date": str(row[0]),
                "merchant": row[1],
                "category": row[2],
                "amount": float(row[3]),
                "notes": row[4]
            })
        
        conn.close()
        return spending_data
        
    except Exception as e:
        print(f"Error fetching data from database: {e}")
        return []

# Build vectorstore from database data at startup
spending_data = get_spending_data_from_db()
vectorstore = build_vectorstore(spending_data)

# Setup RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY")),
    retriever=vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3}),
)

@app.post("/insights")
async def get_insights(request: QueryRequest):
    raw_answer = qa_chain.run(request.query)
    """Get spending insights based on user query"""
    if not raw_answer:
        return {"insight": "No insights found for your query."}
    safe_answer = redact_sensitive(raw_answer)
    return {"insight": safe_answer}

@app.get("/")
async def root():
    return {"message": "Spending Insights API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
