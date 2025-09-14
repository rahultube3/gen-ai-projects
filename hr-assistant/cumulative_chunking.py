"""
Cumulative Text Chunking Implementation
======================================

This module provides clean and efficient cumulative chunking methods:
- Sentence-based cumulative chunking
- Word-based cumulative chunking
- Character-based cumulative chunking
- Smart boundary detection and optimization
- Multiple accumulation strategies
"""

import re
from typing import List, Optional, Union


class CumulativeChunker:
    """
    A focused implementation for cumulative text chunking.
    Cumulative chunking builds chunks by adding content until a threshold is reached.
    """
    
    def __init__(self, max_size: Union[int, float] = 100, 
                 size_unit: str = "words", 
                 preserve_sentences: bool = True,
                 allow_overflow: bool = True):
        """
        Initialize the cumulative chunker.
        
        Args:
            max_size: Maximum size for each chunk
            size_unit: Unit for max_size ("words", "characters", "sentences")
            preserve_sentences: Keep complete sentences when possible
            allow_overflow: Allow chunks to exceed max_size to preserve boundaries
        """
        self.max_size = max_size
        self.size_unit = size_unit.lower()
        self.preserve_sentences = preserve_sentences
        self.allow_overflow = allow_overflow
        self.sentence_pattern = r'[.!?]+\s+'
        
        # Validate size_unit
        if self.size_unit not in ["words", "characters", "sentences"]:
            raise ValueError("size_unit must be 'words', 'characters', or 'sentences'")
    
    def chunk_by_sentences(self, text: str) -> List[str]:
        """
        Cumulative chunking by adding complete sentences.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        # Split into sentences
        sentences = self._split_into_sentences(text)
        if not sentences:
            return []
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = self._calculate_size(sentence)
            
            # Check if adding this sentence would exceed limit
            if current_size + sentence_size > self.max_size and current_chunk:
                # Finalize current chunk
                chunks.append(self._join_sentences(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(self._join_sentences(current_chunk))
        
        return chunks
    
    def chunk_by_words(self, text: str) -> List[str]:
        """
        Cumulative chunking by adding words while respecting sentence boundaries.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        if self.preserve_sentences:
            return self._chunk_words_preserve_sentences(text)
        else:
            return self._chunk_words_simple(text)
    
    def chunk_by_characters(self, text: str) -> List[str]:
        """
        Cumulative chunking by adding characters while respecting boundaries.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        chunks = []
        current_chunk = ""
        
        if self.preserve_sentences:
            sentences = self._split_into_sentences(text)
            
            for sentence in sentences:
                # Check if adding this sentence would exceed limit
                if len(current_chunk) + len(sentence) > self.max_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk = (current_chunk + " " + sentence).strip()
            
            if current_chunk:
                chunks.append(current_chunk.strip())
        else:
            # Simple character-based chunking
            for i in range(0, len(text), int(self.max_size)):
                chunk = text[i:i + int(self.max_size)]
                chunks.append(chunk)
        
        return chunks
    
    def chunk_adaptive(self, text: str) -> List[str]:
        """
        Adaptive cumulative chunking that chooses the best strategy based on text.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        sentences = self._split_into_sentences(text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        # Choose strategy based on average sentence length
        if avg_sentence_length <= self.max_size * 0.3:
            # Short sentences - use sentence-based chunking
            return self.chunk_by_sentences(text)
        elif avg_sentence_length <= self.max_size * 0.8:
            # Medium sentences - use word-based chunking
            return self.chunk_by_words(text)
        else:
            # Long sentences - use character-based chunking
            return self.chunk_by_characters(text)
    
    def chunk_with_context(self, text: str, context_overlap: int = 1) -> List[str]:
        """
        Cumulative chunking with context overlap between chunks.
        
        Args:
            text: Input text to chunk
            context_overlap: Number of sentences to overlap between chunks
            
        Returns:
            List of text chunks with context overlap
        """
        base_chunks = self.chunk_by_sentences(text)
        if len(base_chunks) <= 1 or context_overlap <= 0:
            return base_chunks
        
        # Convert back to sentences for overlap processing
        all_sentences = []
        chunk_boundaries = []
        
        for chunk in base_chunks:
            chunk_sentences = self._split_into_sentences(chunk)
            chunk_boundaries.append(len(all_sentences) + len(chunk_sentences))
            all_sentences.extend(chunk_sentences)
        
        # Create overlapped chunks
        overlapped_chunks = []
        
        for i, boundary in enumerate(chunk_boundaries):
            start_idx = 0 if i == 0 else chunk_boundaries[i-1] - context_overlap
            end_idx = boundary
            
            chunk_sentences = all_sentences[start_idx:end_idx]
            overlapped_chunks.append(self._join_sentences(chunk_sentences))
        
        return overlapped_chunks
    
    def chunk_balanced(self, text: str, target_chunks: int) -> List[str]:
        """
        Create a specific number of balanced cumulative chunks.
        
        Args:
            text: Input text to chunk
            target_chunks: Desired number of chunks
            
        Returns:
            List of balanced text chunks
        """
        if not text or target_chunks <= 0:
            return []
        
        sentences = self._split_into_sentences(text)
        if len(sentences) <= target_chunks:
            return sentences
        
        # Calculate sentences per chunk
        sentences_per_chunk = len(sentences) / target_chunks
        chunks = []
        current_chunk = []
        sentences_in_current = 0
        
        for i, sentence in enumerate(sentences):
            current_chunk.append(sentence)
            sentences_in_current += 1
            
            # Check if we should finalize this chunk
            should_finalize = (
                sentences_in_current >= sentences_per_chunk and 
                len(chunks) < target_chunks - 1
            ) or i == len(sentences) - 1
            
            if should_finalize:
                chunks.append(self._join_sentences(current_chunk))
                current_chunk = []
                sentences_in_current = 0
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        sentences = re.split(self.sentence_pattern, text.strip())
        # Clean and filter sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _calculate_size(self, text: str) -> Union[int, float]:
        """Calculate size of text based on size_unit."""
        if self.size_unit == "words":
            return len(text.split())
        elif self.size_unit == "characters":
            return len(text)
        elif self.size_unit == "sentences":
            return len(self._split_into_sentences(text))
        else:
            return len(text.split())  # Default to words
    
    def _join_sentences(self, sentences: List[str]) -> str:
        """Join sentences with appropriate spacing."""
        if not sentences:
            return ""
        
        result = sentences[0]
        for sentence in sentences[1:]:
            # Add appropriate spacing
            if result.endswith(('.', '!', '?')):
                result += " " + sentence
            else:
                result += ". " + sentence
        
        return result.strip()
    
    def _chunk_words_preserve_sentences(self, text: str) -> List[str]:
        """Word-based chunking while preserving sentence boundaries."""
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            # Check if adding this sentence would exceed word limit
            if current_word_count + sentence_words > self.max_size and current_chunk:
                chunks.append(self._join_sentences(current_chunk))
                current_chunk = [sentence]
                current_word_count = sentence_words
            else:
                current_chunk.append(sentence)
                current_word_count += sentence_words
        
        if current_chunk:
            chunks.append(self._join_sentences(current_chunk))
        
        return chunks
    
    def _chunk_words_simple(self, text: str) -> List[str]:
        """Simple word-based chunking without sentence preservation."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), int(self.max_size)):
            chunk_words = words[i:i + int(self.max_size)]
            chunks.append(' '.join(chunk_words))
        
        return chunks
    
    def get_chunk_statistics(self, chunks: List[str]) -> dict:
        """Get comprehensive statistics about the chunks."""
        if not chunks:
            return {}
        
        word_counts = [len(chunk.split()) for chunk in chunks]
        char_counts = [len(chunk) for chunk in chunks]
        sentence_counts = [len(self._split_into_sentences(chunk)) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_words": sum(word_counts),
            "total_characters": sum(char_counts),
            "total_sentences": sum(sentence_counts),
            "avg_words_per_chunk": sum(word_counts) / len(word_counts),
            "avg_chars_per_chunk": sum(char_counts) / len(char_counts),
            "avg_sentences_per_chunk": sum(sentence_counts) / len(sentence_counts),
            "min_words": min(word_counts),
            "max_words": max(word_counts),
            "min_chars": min(char_counts),
            "max_chars": max(char_counts),
            "size_unit": self.size_unit,
            "max_size_setting": self.max_size
        }


def demonstrate_cumulative_chunking():
    """Demonstrate the cumulative chunking methods."""
    
    # Sample text about AI in healthcare
    sample_text = """
    Artificial Intelligence is revolutionizing healthcare delivery worldwide. Machine learning algorithms can analyze medical images with unprecedented accuracy. Radiologists are now using AI tools to detect cancer earlier than ever before.
    
    Electronic health records contain vast amounts of patient data. Natural language processing helps extract meaningful insights from clinical notes. This enables healthcare providers to identify patterns and improve treatment outcomes.
    
    Drug discovery is another area where AI shows tremendous promise. Traditional pharmaceutical research takes decades and costs billions. AI can accelerate the identification of new compounds and predict their effectiveness.
    
    Personalized medicine is becoming a reality through AI analysis. Genetic data combined with lifestyle factors creates unique patient profiles. Treatment plans can now be tailored to individual characteristics and needs.
    
    Remote patient monitoring uses IoT devices and AI analytics. Continuous health data streams provide real-time insights. Healthcare teams can intervene before conditions become critical emergencies.
    """
    
    print("=== CUMULATIVE CHUNKING DEMONSTRATION ===\n")
    print(f"Original text: {len(sample_text)} characters, {len(sample_text.split())} words\n")
    
    # Method 1: Sentence-based cumulative chunking
    print("1. SENTENCE-BASED CUMULATIVE CHUNKING:")
    print("=" * 55)
    
    sentence_chunker = CumulativeChunker(max_size=30, size_unit="words")
    sentence_chunks = sentence_chunker.chunk_by_sentences(sample_text)
    
    for i, chunk in enumerate(sentence_chunks[:3], 1):  # Show first 3
        word_count = len(chunk.split())
        print(f"\nSentence Chunk {i} ({word_count} words):")
        print("-" * 40)
        print(chunk)
    
    stats = sentence_chunker.get_chunk_statistics(sentence_chunks)
    print(f"\nTotal: {stats['total_chunks']} chunks, avg {stats['avg_words_per_chunk']:.1f} words/chunk")
    
    # Method 2: Word-based cumulative chunking
    print("\n\n2. WORD-BASED CUMULATIVE CHUNKING:")
    print("=" * 55)
    
    word_chunker = CumulativeChunker(max_size=25, size_unit="words", preserve_sentences=True)
    word_chunks = word_chunker.chunk_by_words(sample_text)
    
    for i, chunk in enumerate(word_chunks[:3], 1):  # Show first 3
        word_count = len(chunk.split())
        print(f"\nWord Chunk {i} ({word_count} words):")
        print("-" * 40)
        print(chunk)
    
    stats = word_chunker.get_chunk_statistics(word_chunks)
    print(f"\nTotal: {stats['total_chunks']} chunks, avg {stats['avg_words_per_chunk']:.1f} words/chunk")
    
    # Method 3: Character-based cumulative chunking
    print("\n\n3. CHARACTER-BASED CUMULATIVE CHUNKING:")
    print("=" * 55)
    
    char_chunker = CumulativeChunker(max_size=200, size_unit="characters", preserve_sentences=True)
    char_chunks = char_chunker.chunk_by_characters(sample_text)
    
    for i, chunk in enumerate(char_chunks[:3], 1):  # Show first 3
        char_count = len(chunk)
        print(f"\nChar Chunk {i} ({char_count} chars):")
        print("-" * 40)
        print(chunk[:150] + "..." if len(chunk) > 150 else chunk)
    
    stats = char_chunker.get_chunk_statistics(char_chunks)
    print(f"\nTotal: {stats['total_chunks']} chunks, avg {stats['avg_chars_per_chunk']:.1f} chars/chunk")
    
    # Method 4: Adaptive cumulative chunking
    print("\n\n4. ADAPTIVE CUMULATIVE CHUNKING:")
    print("=" * 55)
    
    adaptive_chunker = CumulativeChunker(max_size=35, size_unit="words")
    adaptive_chunks = adaptive_chunker.chunk_adaptive(sample_text)
    
    for i, chunk in enumerate(adaptive_chunks[:3], 1):  # Show first 3
        word_count = len(chunk.split())
        print(f"\nAdaptive Chunk {i} ({word_count} words):")
        print("-" * 40)
        print(chunk)
    
    stats = adaptive_chunker.get_chunk_statistics(adaptive_chunks)
    print(f"\nTotal: {stats['total_chunks']} chunks, avg {stats['avg_words_per_chunk']:.1f} words/chunk")
    
    # Method 5: Context overlap chunking
    print("\n\n5. CONTEXT OVERLAP CUMULATIVE CHUNKING:")
    print("=" * 55)
    
    context_chunker = CumulativeChunker(max_size=25, size_unit="words")
    context_chunks = context_chunker.chunk_with_context(sample_text, context_overlap=1)
    
    for i, chunk in enumerate(context_chunks[:3], 1):  # Show first 3
        word_count = len(chunk.split())
        print(f"\nContext Chunk {i} ({word_count} words):")
        print("-" * 40)
        print(chunk)
    
    stats = context_chunker.get_chunk_statistics(context_chunks)
    print(f"\nTotal: {stats['total_chunks']} chunks, avg {stats['avg_words_per_chunk']:.1f} words/chunk")
    
    # Method 6: Balanced chunking
    print("\n\n6. BALANCED CUMULATIVE CHUNKING:")
    print("=" * 55)
    
    balanced_chunker = CumulativeChunker(max_size=30, size_unit="words")
    balanced_chunks = balanced_chunker.chunk_balanced(sample_text, target_chunks=4)
    
    for i, chunk in enumerate(balanced_chunks, 1):
        word_count = len(chunk.split())
        print(f"\nBalanced Chunk {i} ({word_count} words):")
        print("-" * 40)
        print(chunk)
    
    stats = balanced_chunker.get_chunk_statistics(balanced_chunks)
    print(f"\nTotal: {stats['total_chunks']} chunks, avg {stats['avg_words_per_chunk']:.1f} words/chunk")
    
    # Summary comparison
    print("\n\n7. COMPARISON SUMMARY:")
    print("=" * 55)
    
    methods = [
        ("Sentence-based", sentence_chunks),
        ("Word-based", word_chunks),
        ("Character-based", char_chunks),
        ("Adaptive", adaptive_chunks),
        ("Context overlap", context_chunks),
        ("Balanced", balanced_chunks)
    ]
    
    print(f"{'Method':<18} {'Chunks':<8} {'Avg Words':<12} {'Min Words':<10} {'Max Words':<10}")
    print("-" * 68)
    
    for method_name, chunks in methods:
        stats = CumulativeChunker().get_chunk_statistics(chunks)
        print(f"{method_name:<18} {stats['total_chunks']:<8} {stats['avg_words_per_chunk']:<12.1f} {stats['min_words']:<10} {stats['max_words']:<10}")


if __name__ == "__main__":
    demonstrate_cumulative_chunking()
