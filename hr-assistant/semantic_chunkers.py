import os
from dotenv import load_dotenv
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI embeddings using API key from .env
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Initialize semantic chunker
semantic_chunker = SemanticChunker(embeddings)

# Example text
# Example text about AI in healthcare
doc = """
Artificial Intelligence (AI) is revolutionizing the healthcare industry worldwide.
Machine learning algorithms are being deployed to assist doctors in medical diagnosis and treatment planning.
Traditional diagnostic methods often rely heavily on physician experience and can miss subtle patterns.
AI systems can analyze vast amounts of medical data including imaging, lab results, and patient histories.
This enables early detection of diseases like cancer, diabetes, and cardiovascular conditions.
Medical professionals are now collaborating with AI tools to provide more accurate and personalized patient care.
"""

# Split into semantic chunks
chunks = semantic_chunker.split_text(doc)

print("Semantic Chunks (using OpenAI embeddings):")
print("Note: These chunks are created based on semantic similarity and meaning")
for i, chunk in enumerate(chunks, 1):
    print(f"\nChunk {i}:\n{chunk}")
