#!/usr/bin/env python3
"""
Interactive Wikipedia RAG Manager
Add any Wikipedia page to your RAG system and query the knowledge
"""
import os
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from wikipedia_rag_scraper import WikipediaRAGIntegrator
from dotenv import load_dotenv
import re

load_dotenv()

class InteractiveWikipediaRAG:
    """Interactive interface for Wikipedia RAG system"""
    
    def __init__(self):
        self.integrator = WikipediaRAGIntegrator("interactive_wiki_knowledge")
        self.added_pages = []
    
    def is_valid_wikipedia_url(self, url: str) -> bool:
        """Check if URL is a valid Wikipedia page"""
        wiki_pattern = r'https?://[a-z]+\.wikipedia\.org/wiki/.+'
        return bool(re.match(wiki_pattern, url))
    
    def show_menu(self):
        """Display the main menu"""
        print("\n🌟 WIKIPEDIA RAG SYSTEM")
        print("="*40)
        print("1. Add Wikipedia page to knowledge base")
        print("2. Query existing knowledge")
        print("3. Show added pages")
        print("4. Show collection statistics")
        print("5. Exit")
        print("-" * 40)
    
    def add_wikipedia_page(self):
        """Add a Wikipedia page to the RAG system"""
        print("\n📚 ADD WIKIPEDIA PAGE")
        print("-" * 30)
        
        # Get URL from user
        url = input("Enter Wikipedia URL: ").strip()
        
        if not url:
            print("❌ Please provide a URL")
            return
        
        if not self.is_valid_wikipedia_url(url):
            print("❌ Please provide a valid Wikipedia URL")
            print("   Example: https://en.wikipedia.org/wiki/Artificial_intelligence")
            return
        
        print(f"\n🕷️ Adding Wikipedia page: {url}")
        
        try:
            success = self.integrator.add_wikipedia_page(url)
            
            if success:
                self.added_pages.append(url)
                print("✅ Successfully added to knowledge base!")
            else:
                print("❌ Failed to add page")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def query_knowledge(self):
        """Query the Wikipedia knowledge base"""
        if self.integrator.collection.count() == 0:
            print("❌ No Wikipedia pages in knowledge base yet!")
            print("   Add some pages first using option 1")
            return
        
        print("\n🔍 QUERY WIKIPEDIA KNOWLEDGE")
        print("-" * 35)
        
        question = input("Enter your question: ").strip()
        
        if not question:
            print("❌ Please provide a question")
            return
        
        print(f"\n🤖 Searching knowledge base...")
        
        try:
            self.integrator.query_wikipedia_knowledge(question)
        except Exception as e:
            print(f"❌ Error querying knowledge: {e}")
    
    def show_added_pages(self):
        """Show all added Wikipedia pages"""
        print("\n📖 ADDED WIKIPEDIA PAGES")
        print("-" * 30)
        
        if not self.added_pages:
            print("No pages added yet")
            return
        
        for i, url in enumerate(self.added_pages, 1):
            page_title = url.split('/')[-1].replace('_', ' ')
            print(f"{i}. {page_title}")
            print(f"   URL: {url}")
            print()
    
    def show_statistics(self):
        """Show collection statistics"""
        print("\n📊 KNOWLEDGE BASE STATISTICS")
        print("-" * 35)
        
        try:
            count = self.integrator.collection.count()
            print(f"Total documents: {count}")
            print(f"Pages added in this session: {len(self.added_pages)}")
            
            if count > 0:
                # Get sample metadata
                sample = self.integrator.collection.get(limit=5)
                if sample and sample.get('metadatas'):
                    print(f"\nSample sources:")
                    seen_titles = set()
                    for meta in sample['metadatas']:
                        if meta and 'page_title' in meta:
                            title = meta['page_title']
                            if title not in seen_titles:
                                seen_titles.add(title)
                                print(f"  • {title}")
                
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
    
    def run(self):
        """Run the interactive system"""
        print("🌟 Welcome to Interactive Wikipedia RAG System!")
        print("Add Wikipedia pages to your knowledge base and ask questions about them.")
        
        # Check if OpenAI API key is configured
        if not os.getenv('OPENAI_API_KEY'):
            print("\n⚠️  WARNING: OpenAI API key not found in .env file")
            print("   The system will work for adding pages but not for generating answers")
        
        while True:
            try:
                self.show_menu()
                choice = input("Select option (1-5): ").strip()
                
                if choice == '1':
                    self.add_wikipedia_page()
                elif choice == '2':
                    self.query_knowledge()
                elif choice == '3':
                    self.show_added_pages()
                elif choice == '4':
                    self.show_statistics()
                elif choice == '5':
                    print("\n👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-5.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")

def quick_demo():
    """Run a quick demonstration"""
    print("🚀 QUICK DEMO: Adding Health Data to RAG")
    print("="*45)
    
    demo_rag = InteractiveWikipediaRAG()
    
    # Add the health data page
    health_url = "https://en.wikipedia.org/wiki/Health_data"
    print(f"Adding: {health_url}")
    
    success = demo_rag.integrator.add_wikipedia_page(health_url)
    
    if success:
        print("\n✅ Health data page added successfully!")
        
        # Ask a sample question
        sample_question = "What is health data and how is it collected?"
        print(f"\n🔍 Sample query: {sample_question}")
        demo_rag.integrator.query_wikipedia_knowledge(sample_question)
        
        print("\n🎉 Demo complete! You can now run the interactive system.")
    else:
        print("❌ Demo failed")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        quick_demo()
    else:
        interactive_rag = InteractiveWikipediaRAG()
        interactive_rag.run()