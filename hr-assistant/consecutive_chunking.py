"""
Consecutive Text Chunking Implementation
=======================================

This module provides clean and efficient consecutive chunking methods:
- Character-based consecutive chunking
- Word-based consecutive chunking  
- Smart boundary preservation
- Configurable overlap options
- Simple and focused API
"""

import re
from typing import List, Optional


class ConsecutiveChunker:
    """
    A focused implementation for consecutive text chunking.
    Provides character-based and word-based chunking with smart boundaries.
    """
    
    def __init__(self, chunk_size: int = 100, overlap: int = 20, 
                 preserve_words: bool = True, preserve_sentences: bool = False):
        """
        Initialize the consecutive chunker.
        
        Args:
            chunk_size: Target size for each chunk
            overlap: Number of characters/words to overlap between chunks
            preserve_words: Avoid breaking words when possible
            preserve_sentences: Avoid breaking sentences when possible
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.preserve_words = preserve_words
        self.preserve_sentences = preserve_sentences
        self.sentence_pattern = r'[.!?]+\s+'
    
    def chunk_by_characters(self, text: str) -> List[str]:
        """
        Split text into consecutive chunks by character count.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        chunks = []
        start = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If we've reached the end of text, take everything remaining
            if end >= len(text):
                remaining = text[start:].strip()
                if remaining:
                    chunks.append(remaining)
                break
            
            # Adjust end position to preserve boundaries
            adjusted_end = self._find_best_break_point(text, start, end)
            
            # Extract chunk
            chunk = text[start:adjusted_end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Calculate next start position with overlap
            start = max(start + 1, adjusted_end - self.overlap)
        
        return chunks
    
    def chunk_by_words(self, text: str) -> List[str]:
        """
        Split text into consecutive chunks by word count.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        words = text.split()
        if not words:
            return []
        
        chunks = []
        start = 0
        
        while start < len(words):
            # Calculate end position
            end = start + self.chunk_size
            
            # Extract words for this chunk
            chunk_words = words[start:end]
            chunk = ' '.join(chunk_words)
            
            # Adjust for sentence boundaries if requested
            if self.preserve_sentences and end < len(words):
                chunk = self._adjust_for_sentence_boundary(chunk, words, start, end)
            
            chunks.append(chunk)
            
            # Calculate next start position with overlap
            start = max(start + 1, end - self.overlap)
        
        return chunks
    
    def chunk_with_fixed_overlap(self, text: str, method: str = "character") -> List[str]:
        """
        Chunk text with guaranteed fixed overlap between consecutive chunks.
        
        Args:
            text: Input text to chunk
            method: "character" or "word" based chunking
            
        Returns:
            List of text chunks with consistent overlap
        """
        if method == "character":
            return self._chunk_chars_fixed_overlap(text)
        elif method == "word":
            return self._chunk_words_fixed_overlap(text)
        else:
            raise ValueError("Method must be 'character' or 'word'")
    
    def chunk_sliding_window(self, text: str, step_size: Optional[int] = None) -> List[str]:
        """
        Create chunks using a sliding window approach.
        
        Args:
            text: Input text to chunk
            step_size: How many characters to move for each chunk (default: chunk_size - overlap)
            
        Returns:
            List of overlapping text chunks
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        if step_size is None:
            step_size = max(1, self.chunk_size - self.overlap)
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end > len(text):
                # Last chunk - include remaining text
                remaining = text[start:].strip()
                if remaining and len(remaining) > self.chunk_size // 4:  # Avoid tiny chunks
                    chunks.append(remaining)
                break
            
            # Adjust for word boundaries if needed
            if self.preserve_words:
                adjusted_end = self._find_word_boundary(text, end, start)
                chunk = text[start:adjusted_end].strip()
            else:
                chunk = text[start:end].strip()
            
            if chunk:
                chunks.append(chunk)
            
            start += step_size
        
        return chunks
    
    def _find_best_break_point(self, text: str, start: int, end: int) -> int:
        """Find the best position to break text, preserving boundaries."""
        if end >= len(text):
            return len(text)
        
        original_end = end
        
        # Try to preserve sentence boundaries first
        if self.preserve_sentences:
            sentence_end = self._find_sentence_boundary(text, end, start)
            if sentence_end != end:
                return sentence_end
        
        # Try to preserve word boundaries
        if self.preserve_words:
            word_end = self._find_word_boundary(text, end, start)
            if word_end != end:
                return word_end
        
        return original_end
    
    def _find_sentence_boundary(self, text: str, end: int, start: int) -> int:
        """Find a good sentence boundary near the end position."""
        # Look backward for sentence ending
        search_range = min(50, end - start)  # Don't search too far back
        
        for i in range(end, max(start, end - search_range), -1):
            if i < len(text) - 1 and text[i] in '.!?':
                # Check if followed by whitespace (actual sentence end)
                if i + 1 < len(text) and text[i + 1].isspace():
                    return i + 1
        
        return end
    
    def _find_word_boundary(self, text: str, end: int, start: int) -> int:
        """Find a good word boundary near the end position."""
        # Look backward for whitespace
        search_range = min(30, end - start)  # Don't search too far back
        
        for i in range(end, max(start, end - search_range), -1):
            if i < len(text) and text[i].isspace():
                return i
        
        return end
    
    def _adjust_for_sentence_boundary(self, chunk: str, words: List[str], 
                                    start: int, end: int) -> str:
        """Adjust word-based chunk to end at sentence boundary."""
        # Check if chunk ends mid-sentence
        if not re.search(r'[.!?]\s*$', chunk):
            # Look for sentence ending in next few words
            for i in range(end, min(len(words), end + 5)):
                if re.search(r'[.!?]$', words[i]):
                    # Include words up to sentence end
                    extended_words = words[start:i+1]
                    return ' '.join(extended_words)
        
        return chunk
    
    def _chunk_chars_fixed_overlap(self, text: str) -> List[str]:
        """Character-based chunking with guaranteed fixed overlap."""
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Move exactly by (chunk_size - overlap)
            start += self.chunk_size - self.overlap
        
        return chunks
    
    def _chunk_words_fixed_overlap(self, text: str) -> List[str]:
        """Word-based chunking with guaranteed fixed overlap."""
        words = text.split()
        if not words:
            return []
        
        chunks = []
        start = 0
        
        while start < len(words):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            chunks.append(' '.join(chunk_words))
            
            # Move exactly by (chunk_size - overlap)
            start += self.chunk_size - self.overlap
        
        return chunks
    
    def get_chunk_info(self, chunks: List[str]) -> dict:
        """Get information about the chunks."""
        if not chunks:
            return {}
        
        word_counts = [len(chunk.split()) for chunk in chunks]
        char_counts = [len(chunk) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_chars_per_chunk": sum(char_counts) / len(char_counts),
            "avg_words_per_chunk": sum(word_counts) / len(word_counts),
            "min_chars": min(char_counts),
            "max_chars": max(char_counts),
            "min_words": min(word_counts),
            "max_words": max(word_counts),
            "total_chars": sum(char_counts),
            "total_words": sum(word_counts)
        }


def demonstrate_consecutive_chunking():
    """Demonstrate the consecutive chunking methods."""
    
    # Sample text
    sample_text = """
    Artificial Intelligence is revolutionizing healthcare delivery worldwide. Machine learning algorithms can analyze medical images with unprecedented accuracy. Radiologists are now using AI tools to detect cancer earlier than ever before.
    
    Electronic health records contain vast amounts of patient data. Natural language processing helps extract meaningful insights from clinical notes. This enables healthcare providers to identify patterns and improve treatment outcomes.
    
    Drug discovery is another area where AI shows tremendous promise. Traditional pharmaceutical research takes decades and costs billions. AI can accelerate the identification of new compounds and predict their effectiveness.
    """
    
    print("=== CONSECUTIVE CHUNKING DEMONSTRATION ===\n")
    print(f"Original text: {len(sample_text)} characters, {len(sample_text.split())} words\n")
    
    # Method 1: Character-based chunking
    print("1. CHARACTER-BASED CONSECUTIVE CHUNKING:")
    print("=" * 50)
    
    chunker = ConsecutiveChunker(chunk_size=150, overlap=30, preserve_words=True)
    char_chunks = chunker.chunk_by_characters(sample_text)
    
    for i, chunk in enumerate(char_chunks[:3], 1):  # Show first 3
        print(f"\nChunk {i} ({len(chunk)} chars):")
        print("-" * 30)
        print(chunk)
    
    info = chunker.get_chunk_info(char_chunks)
    print(f"\nTotal: {info['total_chunks']} chunks, avg {info['avg_chars_per_chunk']:.1f} chars/chunk")
    
    # Method 2: Word-based chunking
    print("\n\n2. WORD-BASED CONSECUTIVE CHUNKING:")
    print("=" * 50)
    
    word_chunker = ConsecutiveChunker(chunk_size=25, overlap=5, preserve_sentences=True)
    word_chunks = word_chunker.chunk_by_words(sample_text)
    
    for i, chunk in enumerate(word_chunks[:3], 1):  # Show first 3
        print(f"\nChunk {i} ({len(chunk.split())} words):")
        print("-" * 30)
        print(chunk)
    
    info = word_chunker.get_chunk_info(word_chunks)
    print(f"\nTotal: {info['total_chunks']} chunks, avg {info['avg_words_per_chunk']:.1f} words/chunk")
    
    # Method 3: Sliding window chunking
    print("\n\n3. SLIDING WINDOW CONSECUTIVE CHUNKING:")
    print("=" * 50)
    
    sliding_chunker = ConsecutiveChunker(chunk_size=120, overlap=40, preserve_words=True)
    sliding_chunks = sliding_chunker.chunk_sliding_window(sample_text)
    
    for i, chunk in enumerate(sliding_chunks[:3], 1):  # Show first 3
        print(f"\nSliding Chunk {i} ({len(chunk)} chars):")
        print("-" * 30)
        print(chunk)
    
    info = sliding_chunker.get_chunk_info(sliding_chunks)
    print(f"\nTotal: {info['total_chunks']} chunks, avg {info['avg_chars_per_chunk']:.1f} chars/chunk")
    
    # Method 4: Fixed overlap chunking
    print("\n\n4. FIXED OVERLAP CONSECUTIVE CHUNKING:")
    print("=" * 50)
    
    fixed_chunker = ConsecutiveChunker(chunk_size=100, overlap=25)
    fixed_chunks = fixed_chunker.chunk_with_fixed_overlap(sample_text, method="character")
    
    for i, chunk in enumerate(fixed_chunks[:3], 1):  # Show first 3
        print(f"\nFixed Overlap Chunk {i} ({len(chunk)} chars):")
        print("-" * 30)
        print(chunk[:80] + "..." if len(chunk) > 80 else chunk)
    
    info = fixed_chunker.get_chunk_info(fixed_chunks)
    print(f"\nTotal: {info['total_chunks']} chunks, avg {info['avg_chars_per_chunk']:.1f} chars/chunk")
    
    # Summary comparison
    print("\n\n5. COMPARISON SUMMARY:")
    print("=" * 50)
    methods = [
        ("Character-based", char_chunks),
        ("Word-based", word_chunks),
        ("Sliding window", sliding_chunks),
        ("Fixed overlap", fixed_chunks)
    ]
    
    print(f"{'Method':<20} {'Chunks':<8} {'Avg Chars':<12} {'Avg Words':<10}")
    print("-" * 50)
    
    for method_name, chunks in methods:
        info = ConsecutiveChunker().get_chunk_info(chunks)
        print(f"{method_name:<20} {info['total_chunks']:<8} {info['avg_chars_per_chunk']:<12.1f} {info['avg_words_per_chunk']:<10.1f}")


if __name__ == "__main__":
    demonstrate_consecutive_chunking()