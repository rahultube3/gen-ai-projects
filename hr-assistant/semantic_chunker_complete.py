"""
Complete Semantic Chunker Example
This script shows how to use real semantic chunking with embeddings.

Requirements:
- pip install langchain-experimental
- pip install langchain-openai (for OpenAI embeddings) OR
- pip install sentence-transformers (for HuggingFace embeddings)
- pip install torch (for HuggingFace embeddings)

Note: For OpenAI embeddings, you need to set OPENAI_API_KEY environment variable
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Uncomment the following lines if you have the dependencies installed:

# Option 1: Using OpenAI embeddings (requires API key)
# from langchain_experimental.text_splitter import SemanticChunker
# from langchain_openai import OpenAIEmbeddings
# embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Option 2: Using HuggingFace embeddings (free, but requires torch)
# from langchain_experimental.text_splitter import SemanticChunker
# from langchain_community.embeddings import HuggingFaceEmbeddings
# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# semantic_chunker = SemanticChunker(embeddings)

# For now, using character-based splitting as demo
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50,
    length_function=len,
)

# Example text about AI and fraud detection
doc = """
Artificial Intelligence (AI) is rapidly transforming industries across the globe.
One of the most promising applications is in financial services, particularly fraud detection.

Machine learning models are increasingly being used to detect fraudulent transactions in banking.
These systems can analyze patterns in transaction data to identify suspicious activities.
Traditional rule-based systems are often too rigid and generate many false positives.

In contrast, AI-powered fraud detection systems learn patterns of normal and abnormal activity from historical data.
They can adapt to new fraud patterns and reduce false positives significantly.
This allows them to flag suspicious transactions with greater accuracy and efficiency.

Banks are now combining AI algorithms with human oversight for optimal fraud detection.
This hybrid approach leverages the speed and pattern recognition of AI while maintaining human judgment for complex cases.
The result is more effective fraud prevention and better customer experience.

Furthermore, real-time processing capabilities of modern AI systems enable immediate transaction monitoring.
This means fraudulent activities can be detected and stopped within seconds of occurrence.
Such rapid response times are crucial in preventing financial losses and protecting customer accounts.
"""

def demonstrate_chunking():
    print("=== TEXT CHUNKING DEMONSTRATION ===\n")
    print("Original text length:", len(doc), "characters\n")
    
    # Character-based chunking (current implementation)
    print("1. CHARACTER-BASED CHUNKING (Current Demo):")
    print("-" * 50)
    chunks = text_splitter.split_text(doc)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i} ({len(chunk)} chars):")
        print(chunk)
    
    print(f"\nTotal chunks created: {len(chunks)}")
    
    # Semantic chunking explanation
    print("\n\n2. SEMANTIC CHUNKING (Requires Dependencies):")
    print("-" * 50)
    print("With proper semantic chunking, chunks would be created based on:")
    print("• Semantic similarity between sentences")
    print("• Topic boundaries in the text")
    print("• Conceptual coherence")
    print("• Meaning-based relationships")
    print("\nExample semantic chunks might be:")
    print("• Chunk 1: Introduction to AI and its applications")
    print("• Chunk 2: Traditional vs AI fraud detection systems")
    print("• Chunk 3: Benefits of hybrid AI-human approach")
    print("• Chunk 4: Real-time processing capabilities")
    
    # Show how to install dependencies
    print("\n\n3. TO ENABLE SEMANTIC CHUNKING:")
    print("-" * 50)
    print("Install required packages:")
    print("pip install langchain-experimental")
    print("pip install sentence-transformers  # for HuggingFace embeddings")
    print("pip install torch  # required by sentence-transformers")
    print("\nOr for OpenAI embeddings:")
    print("pip install langchain-openai")
    print("export OPENAI_API_KEY='your-api-key-here'")

if __name__ == "__main__":
    demonstrate_chunking()