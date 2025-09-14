"""
Statistical Text Chunking Methods
This script demonstrates various statistical approaches to text chunking,
including sentence-based, paragraph-based, and statistical boundary detection.
"""

import re
import numpy as np
from typing import List, Tuple
from collections import Counter
import statistics


class StatisticalChunker:
    """
    A class that implements various statistical methods for text chunking.
    """
    
    def __init__(self):
        self.sentence_pattern = r'[.!?]+\s+'
        self.paragraph_pattern = r'\n\s*\n'
    
    def chunk_by_sentences(self, text: str, sentences_per_chunk: int = 3) -> List[str]:
        """
        Chunk text by grouping sentences together.
        """
        sentences = re.split(self.sentence_pattern, text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        for i in range(0, len(sentences), sentences_per_chunk):
            chunk = '. '.join(sentences[i:i + sentences_per_chunk])
            if chunk:
                chunks.append(chunk + '.')
        
        return chunks
    
    def chunk_by_paragraphs(self, text: str) -> List[str]:
        """
        Chunk text by natural paragraph breaks.
        """
        paragraphs = re.split(self.paragraph_pattern, text.strip())
        return [p.strip() for p in paragraphs if p.strip()]
    
    def chunk_by_word_count(self, text: str, words_per_chunk: int = 50, overlap: int = 10) -> List[str]:
        """
        Chunk text based on word count with optional overlap.
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), words_per_chunk - overlap):
            chunk_words = words[i:i + words_per_chunk]
            if chunk_words:
                chunks.append(' '.join(chunk_words))
        
        return chunks
    
    def chunk_by_statistical_boundaries(self, text: str, window_size: int = 5) -> List[str]:
        """
        Use statistical methods to find natural boundaries in text.
        Based on vocabulary changes and sentence length variations.
        """
        sentences = re.split(r'[.!?]+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= window_size:
            return [text]
        
        # Calculate statistics for each sentence
        sentence_stats = []
        for sentence in sentences:
            words = sentence.split()
            stats = {
                'length': len(words),
                'avg_word_length': np.mean([len(word) for word in words]) if words else 0,
                'vocab_diversity': len(set(word.lower() for word in words)) / len(words) if words else 0
            }
            sentence_stats.append(stats)
        
        # Find boundary points based on statistical changes
        boundaries = [0]
        
        for i in range(window_size, len(sentences) - window_size):
            # Calculate statistics for windows before and after current position
            before_window = sentence_stats[i-window_size:i]
            after_window = sentence_stats[i:i+window_size]
            
            # Calculate means for each statistic
            before_length = np.mean([s['length'] for s in before_window])
            after_length = np.mean([s['length'] for s in after_window])
            
            before_vocab = np.mean([s['vocab_diversity'] for s in before_window])
            after_vocab = np.mean([s['vocab_diversity'] for s in after_window])
            
            # If there's a significant change, mark as boundary
            length_change = abs(before_length - after_length) / max(before_length, after_length, 1)
            vocab_change = abs(before_vocab - after_vocab) / max(before_vocab, after_vocab, 0.01)
            
            if length_change > 0.3 or vocab_change > 0.3:
                boundaries.append(i)
        
        boundaries.append(len(sentences))
        
        # Create chunks based on boundaries
        chunks = []
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            chunk_sentences = sentences[start:end]
            chunks.append('. '.join(chunk_sentences) + '.')
        
        return chunks
    
    def get_chunk_statistics(self, chunks: List[str]) -> dict:
        """
        Calculate statistics about the chunks.
        """
        if not chunks:
            return {}
        
        word_counts = [len(chunk.split()) for chunk in chunks]
        char_counts = [len(chunk) for chunk in chunks]
        
        return {
            'num_chunks': len(chunks),
            'avg_words_per_chunk': statistics.mean(word_counts),
            'median_words_per_chunk': statistics.median(word_counts),
            'std_words_per_chunk': statistics.stdev(word_counts) if len(word_counts) > 1 else 0,
            'avg_chars_per_chunk': statistics.mean(char_counts),
            'min_words': min(word_counts),
            'max_words': max(word_counts),
            'total_words': sum(word_counts)
        }


def demonstrate_statistical_chunking():
    """
    Demonstrate different statistical chunking methods.
    """
    
    # Sample text about AI in healthcare
    sample_text  = """
Artificial Intelligence (AI) is revolutionizing the healthcare industry worldwide.
Machine learning algorithms are being deployed to assist doctors in medical diagnosis and treatment planning.
Traditional diagnostic methods often rely heavily on physician experience and can miss subtle patterns.
AI systems can analyze vast amounts of medical data including imaging, lab results, and patient histories.
This enables early detection of diseases like cancer, diabetes, and cardiovascular conditions.
Medical professionals are now collaborating with AI tools to provide more accurate and personalized patient care.
"""
    
    chunker = StatisticalChunker()
    
    print("=== STATISTICAL TEXT CHUNKING DEMONSTRATION ===\n")
    print(f"Original text length: {len(sample_text)} characters")
    print(f"Word count: {len(sample_text.split())} words\n")
    
    # Method 1: Sentence-based chunking
    print("1. SENTENCE-BASED CHUNKING (3 sentences per chunk):")
    print("=" * 60)
    sentence_chunks = chunker.chunk_by_sentences(sample_text, sentences_per_chunk=3)
    
    for i, chunk in enumerate(sentence_chunks, 1):
        print(f"\nSentence Chunk {i} ({len(chunk.split())} words):")
        print("-" * 40)
        print(chunk)
    
    stats = chunker.get_chunk_statistics(sentence_chunks)
    print(f"\nStatistics: {stats['num_chunks']} chunks, avg {stats['avg_words_per_chunk']:.1f} words/chunk")
    
    # Method 2: Paragraph-based chunking
    print("\n\n2. PARAGRAPH-BASED CHUNKING:")
    print("=" * 60)
    paragraph_chunks = chunker.chunk_by_paragraphs(sample_text)
    
    for i, chunk in enumerate(paragraph_chunks, 1):
        print(f"\nParagraph Chunk {i} ({len(chunk.split())} words):")
        print("-" * 40)
        print(chunk)
    
    stats = chunker.get_chunk_statistics(paragraph_chunks)
    print(f"\nStatistics: {stats['num_chunks']} chunks, avg {stats['avg_words_per_chunk']:.1f} words/chunk")
    
    # Method 3: Word count-based chunking
    print("\n\n3. WORD COUNT-BASED CHUNKING (50 words per chunk):")
    print("=" * 60)
    word_chunks = chunker.chunk_by_word_count(sample_text, words_per_chunk=50, overlap=5)
    
    for i, chunk in enumerate(word_chunks, 1):
        print(f"\nWord Count Chunk {i} ({len(chunk.split())} words):")
        print("-" * 40)
        print(chunk)
    
    stats = chunker.get_chunk_statistics(word_chunks)
    print(f"\nStatistics: {stats['num_chunks']} chunks, avg {stats['avg_words_per_chunk']:.1f} words/chunk")
    
    # Method 4: Statistical boundary detection
    print("\n\n4. STATISTICAL BOUNDARY DETECTION:")
    print("=" * 60)
    statistical_chunks = chunker.chunk_by_statistical_boundaries(sample_text, window_size=2)
    
    for i, chunk in enumerate(statistical_chunks, 1):
        print(f"\nStatistical Chunk {i} ({len(chunk.split())} words):")
        print("-" * 40)
        print(chunk)
    
    stats = chunker.get_chunk_statistics(statistical_chunks)
    print(f"\nStatistics: {stats['num_chunks']} chunks, avg {stats['avg_words_per_chunk']:.1f} words/chunk")
    
    # Comparison summary
    print("\n\n5. COMPARISON SUMMARY:")
    print("=" * 60)
    methods = [
        ("Sentence-based", sentence_chunks),
        ("Paragraph-based", paragraph_chunks),
        ("Word count-based", word_chunks),
        ("Statistical boundaries", statistical_chunks)
    ]
    
    print(f"{'Method':<20} {'Chunks':<8} {'Avg Words':<12} {'Std Dev':<10}")
    print("-" * 50)
    
    for method_name, chunks in methods:
        stats = chunker.get_chunk_statistics(chunks)
        print(f"{method_name:<20} {stats['num_chunks']:<8} {stats['avg_words_per_chunk']:<12.1f} {stats['std_words_per_chunk']:<10.1f}")
    
    print("\nKey Insights:")
    print("• Paragraph-based chunking respects natural document structure")
    print("• Word count-based chunking provides consistent sizes")
    print("• Sentence-based chunking maintains semantic coherence")
    print("• Statistical boundaries detect topic shifts automatically")


if __name__ == "__main__":
    demonstrate_statistical_chunking()
