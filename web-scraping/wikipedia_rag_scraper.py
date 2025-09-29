#!/usr/bin/env python3
"""
Wikipedia Web Scraper for RAG System
General-purpose Wikipedia scraper that integrates with existing ChromaDB + OpenAI RAG
"""
import os
import requests
from bs4 import BeautifulSoup
import chromadb
from dotenv import load_dotenv
from openai import OpenAI
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import time
import json

# Load environment variables
load_dotenv()

class WikipediaScraper:
    """General-purpose Wikipedia scraper"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Educational RAG System 1.0 (https://github.com/educational/rag)'
        })
    
    def extract_wikipedia_content(self, url: str) -> Optional[Dict]:
        """Extract structured content from any Wikipedia page"""
        print(f"📖 Scraping Wikipedia: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract page title
            title_element = soup.find('h1', {'id': 'firstHeading'})
            title = title_element.get_text().strip() if title_element else "Unknown Title"
            
            # Extract main content
            content_div = soup.find('div', {'id': 'mw-content-text'})
            if not content_div:
                raise Exception("Could not find main content div")
            
            # Get introduction (first few paragraphs before first heading)
            introduction = self._extract_introduction(content_div)
            
            # Extract sections
            sections = self._extract_sections(content_div)
            
            # Extract infobox
            infobox = self._extract_infobox(soup)
            
            # Extract categories
            categories = self._extract_categories(soup)
            
            # Extract references count
            references = self._count_references(soup)
            
            # Extract images
            images = self._extract_images(content_div, url)
            
            print(f"✅ Extracted content from '{title}':")
            print(f"   • Introduction: {len(introduction.split())} words")
            print(f"   • Sections: {len(sections)}")
            print(f"   • Infobox items: {len(infobox)}")
            print(f"   • Categories: {len(categories)}")
            print(f"   • References: {references}")
            
            return {
                "title": title,
                "url": url,
                "introduction": introduction,
                "sections": sections,
                "infobox": infobox,
                "categories": categories,
                "references_count": references,
                "images": images,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "word_count": len(introduction.split()) + sum(len(s['content'].split()) for s in sections)
            }
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return None
    
    def _extract_introduction(self, content_div) -> str:
        """Extract the introduction section (before first heading)"""
        intro_paragraphs = []
        
        for element in content_div.find_all(['p', 'h2'], recursive=True):
            if element.name == 'h2':
                break  # Stop at first heading
            if element.name == 'p':
                text = self._clean_text(element.get_text())
                if text and len(text) > 20:
                    intro_paragraphs.append(text)
        
        return "\n\n".join(intro_paragraphs)
    
    def _extract_sections(self, content_div) -> List[Dict]:
        """Extract all sections with their content"""
        sections = []
        current_section = None
        
        for element in content_div.find_all(['h2', 'h3', 'h4', 'p', 'ul', 'ol']):
            if element.name in ['h2', 'h3', 'h4']:
                # Save previous section
                if current_section and current_section['content'].strip():
                    sections.append(current_section)
                
                # Start new section
                header_text = self._clean_text(element.get_text())
                header_text = re.sub(r'\[edit\]', '', header_text).strip()
                
                if header_text:
                    current_section = {
                        "title": header_text,
                        "level": int(element.name[1]),  # h2=2, h3=3, etc.
                        "content": ""
                    }
            
            elif current_section and element.name == 'p':
                text = self._clean_text(element.get_text())
                if text and len(text) > 15:
                    current_section['content'] += text + "\n\n"
            
            elif current_section and element.name in ['ul', 'ol']:
                list_content = self._extract_list_content(element)
                if list_content:
                    current_section['content'] += list_content + "\n\n"
        
        # Add final section
        if current_section and current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _extract_list_content(self, list_element) -> str:
        """Extract content from ul/ol elements"""
        items = []
        for li in list_element.find_all('li', recursive=False):
            item_text = self._clean_text(li.get_text())
            if item_text:
                items.append(f"• {item_text}")
        return "\n".join(items) if items else ""
    
    def _extract_infobox(self, soup) -> Dict:
        """Extract infobox data"""
        infobox_data = {}
        infobox = soup.find('table', class_='infobox')
        
        if infobox:
            rows = infobox.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) == 2:
                    key = self._clean_text(cells[0].get_text())
                    value = self._clean_text(cells[1].get_text())
                    if key and value:
                        infobox_data[key] = value
        
        return infobox_data
    
    def _extract_categories(self, soup) -> List[str]:
        """Extract page categories"""
        categories = []
        cat_links = soup.find_all('a', href=re.compile(r'/wiki/Category:'))
        
        for link in cat_links:
            cat_name = link.get_text().strip()
            if cat_name and cat_name not in categories:
                categories.append(cat_name)
        
        return categories[:20]  # Limit to top 20 categories
    
    def _count_references(self, soup) -> int:
        """Count the number of references"""
        ref_section = soup.find('ol', class_='references')
        if ref_section:
            return len(ref_section.find_all('li'))
        return 0
    
    def _extract_images(self, content_div, base_url: str) -> List[Dict]:
        """Extract image information"""
        images = []
        img_elements = content_div.find_all('img')[:5]  # Limit to 5 images
        
        for img in img_elements:
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src and alt:
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(base_url, src)
                
                images.append({
                    "src": src,
                    "alt": self._clean_text(alt),
                    "width": img.get('width', ''),
                    "height": img.get('height', '')
                })
        
        return images
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove citations [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove edit links
        text = re.sub(r'\[edit\]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special Wikipedia markup
        text = re.sub(r'\(listen\)', '', text)
        text = re.sub(r'\(help·info\)', '', text)
        
        return text.strip()

class WikipediaRAGIntegrator:
    """Integrates Wikipedia content with existing RAG system"""
    
    def __init__(self, collection_name: str = "wikipedia_knowledge"):
        self.scraper = WikipediaScraper()
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Wikipedia content for RAG system"}
        )
    
    def add_wikipedia_page(self, url: str) -> bool:
        """Scrape and add a Wikipedia page to the RAG system"""
        print(f"\n📚 Adding Wikipedia page to RAG system")
        print(f"🌐 URL: {url}")
        
        # Scrape the content
        scraped_data = self.scraper.extract_wikipedia_content(url)
        
        if not scraped_data:
            print("❌ Failed to scrape Wikipedia page")
            return False
        
        # Prepare documents for ingestion
        documents = []
        metadatas = []
        ids = []
        doc_counter = 0
        
        # Add introduction as a document
        if scraped_data['introduction']:
            documents.append(f"Introduction to {scraped_data['title']}\n\n{scraped_data['introduction']}")
            metadatas.append({
                "source": "wikipedia",
                "url": url,
                "page_title": scraped_data['title'],
                "section_title": "Introduction",
                "section_type": "introduction",
                "word_count": len(scraped_data['introduction'].split()),
                "scraped_at": scraped_data['scraped_at']
            })
            ids.append(f"wiki_{hash(url)}_{doc_counter}")
            doc_counter += 1
        
        # Add sections as separate documents
        for section in scraped_data['sections']:
            if len(section['content'].strip()) >= 100:  # Only substantial sections
                content = f"Section: {section['title']}\nLevel: {section['level']}\n\n{section['content']}"
                
                documents.append(content)
                metadatas.append({
                    "source": "wikipedia",
                    "url": url,
                    "page_title": scraped_data['title'],
                    "section_title": section['title'],
                    "section_type": f"heading_level_{section['level']}",
                    "word_count": len(section['content'].split()),
                    "scraped_at": scraped_data['scraped_at']
                })
                ids.append(f"wiki_{hash(url)}_{doc_counter}")
                doc_counter += 1
        
        # Add infobox as summary document
        if scraped_data['infobox']:
            infobox_content = f"Key Facts about {scraped_data['title']}\n\n"
            for key, value in scraped_data['infobox'].items():
                infobox_content += f"{key}: {value}\n"
            
            documents.append(infobox_content)
            metadatas.append({
                "source": "wikipedia",
                "url": url,
                "page_title": scraped_data['title'],
                "section_title": "Key Facts",
                "section_type": "infobox",
                "word_count": len(infobox_content.split()),
                "scraped_at": scraped_data['scraped_at']
            })
            ids.append(f"wiki_{hash(url)}_infobox")
            doc_counter += 1
        
        # Add to ChromaDB
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ Added {len(documents)} documents to RAG system")
            print(f"📄 Page: {scraped_data['title']}")
            print(f"📊 Total words: {scraped_data['word_count']}")
            print(f"🏷️ Categories: {', '.join(scraped_data['categories'][:3])}...")
            
            return True
        
        return False
    
    def query_wikipedia_knowledge(self, question: str, n_results: int = 3):
        """Query Wikipedia knowledge in the RAG system"""
        print(f"\n🔍 Wikipedia Query: {question}")
        
        # Search ChromaDB
        search_results = self.collection.query(
            query_texts=[question],
            n_results=n_results,
            where={"source": "wikipedia"}
        )
        
        if not search_results['documents'][0]:
            return "No relevant Wikipedia content found for this question."
        
        # Prepare context
        context_parts = []
        for doc, metadata in zip(search_results['documents'][0], search_results['metadatas'][0]):
            context_parts.append(f"From '{metadata['page_title']}' - {metadata['section_title']}:\n{doc}")
        
        context = "\n\n".join(context_parts)
        
        # Generate answer with OpenAI
        system_prompt = """You are a knowledgeable assistant with access to Wikipedia information. 
        Provide accurate, well-structured answers based on the Wikipedia content provided. 
        Cite specific sections when relevant and explain complex topics clearly."""
        
        user_prompt = f"""Question: {question}

Wikipedia Content:
{context}

Please provide a comprehensive answer based on the Wikipedia information above."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            
            print(f"🤖 Answer:")
            print(answer)
            
            return answer
            
        except Exception as e:
            print(f"❌ Error generating answer: {e}")
            return f"Error generating answer: {e}"

def demo_wikipedia_rag():
    """Demonstrate Wikipedia RAG system"""
    print("🌟 WIKIPEDIA RAG DEMONSTRATION")
    print("="*50)
    
    # Initialize integrator
    integrator = WikipediaRAGIntegrator("wikipedia_knowledge")
    
    # Add the health data page
    health_data_url = "https://en.wikipedia.org/wiki/Health_data"
    success = integrator.add_wikipedia_page(health_data_url)
    
    if success:
        # Test some queries
        test_queries = [
            "What is health data?",
            "How is health data used in healthcare?",
            "What are the main challenges with health data?",
            "What types of health data exist?"
        ]
        
        print(f"\n🧪 Testing Wikipedia RAG with {len(test_queries)} queries")
        print("="*55)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"QUERY {i}: {query}")
            print('='*60)
            integrator.query_wikipedia_knowledge(query)
            time.sleep(1)  # Brief pause
    
    print(f"\n✨ Wikipedia RAG demonstration complete!")
    print(f"📊 Collection now contains: {integrator.collection.count()} documents")

if __name__ == "__main__":
    demo_wikipedia_rag()