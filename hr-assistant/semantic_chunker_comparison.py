import os
from dotenv import load_dotenv
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI embeddings using API key from .env
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Initialize semantic chunker
semantic_chunker = SemanticChunker(embeddings)

# Initialize character-based chunker for comparison
character_chunker = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50,
    length_function=len,
)

# Extended example text
doc = """
Artificial Intelligence (AI) is revolutionizing the healthcare industry worldwide.
Machine learning algorithms are being deployed to assist doctors in medical diagnosis and treatment planning.
Traditional diagnostic methods often rely heavily on physician experience and can miss subtle patterns.
AI systems can analyze vast amounts of medical data including imaging, lab results, and patient histories.
This enables early detection of diseases like cancer, diabetes, and cardiovascular conditions.
Medical professionals are now collaborating with AI tools to provide more accurate and personalized patient care.
"""

def compare_chunking_methods():
    print("=== SEMANTIC vs CHARACTER-BASED CHUNKING COMPARISON ===\n")
    print(f"Original text length: {len(doc)} characters\n")
    
    # Semantic chunking
    print("1. SEMANTIC CHUNKING (OpenAI Embeddings):")
    print("=" * 60)
    semantic_chunks = semantic_chunker.split_text(doc)
    
    for i, chunk in enumerate(semantic_chunks, 1):
        print(f"\nSemantic Chunk {i} ({len(chunk)} chars):")
        print("-" * 40)
        print(chunk.strip())
    
    print(f"\nTotal semantic chunks: {len(semantic_chunks)}")
    
    # Character-based chunking
    print("\n\n2. CHARACTER-BASED CHUNKING:")
    print("=" * 60)
    character_chunks = character_chunker.split_text(doc)
    
    for i, chunk in enumerate(character_chunks, 1):
        print(f"\nCharacter Chunk {i} ({len(chunk)} chars):")
        print("-" * 40)
        print(chunk.strip())
    
    print(f"\nTotal character chunks: {len(character_chunks)}")
    
    # Analysis
    print("\n\n3. ANALYSIS:")
    print("=" * 60)
    print("Key Differences:")
    print("• Semantic chunking groups related concepts together")
    print("• Character chunking splits based on fixed length")
    print("• Semantic chunks preserve topic coherence")
    print("• Character chunks may break sentences mid-thought")
    print(f"• Semantic chunking created {len(semantic_chunks)} chunks")
    print(f"• Character chunking created {len(character_chunks)} chunks")

if __name__ == "__main__":
    try:
        compare_chunking_methods()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your OPENAI_API_KEY is set in the .env file")