#!/usr/bin/env python3
"""
Wikipedia Health Data Web Scraper for RAG System
Scrapes health data information and integrates it with ChromaDB + OpenAI
"""
import os
import requests
from bs4 import BeautifulSoup
import chromadb
from dotenv import load_dotenv
from openai import OpenAI
import re
from typing import List, Dict
from urllib.parse import urljoin
import time

# Load environment variables
load_dotenv()

class HealthDataScraper:
    """Scraper for health data information"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_wikipedia_health_data(self, url: str) -> Dict:
        """Scrape the Wikipedia health data page"""
        print(f"🕷️ Scraping: {url}")
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract main content
            content_div = soup.find('div', {'id': 'mw-content-text'})
            if not content_div:
                raise Exception("Could not find main content div")
            
            # Extract title
            title = soup.find('h1', {'id': 'firstHeading'}).get_text().strip()
            
            # Extract sections
            sections = []
            current_section = {"title": "Introduction", "content": ""}
            
            for element in content_div.find_all(['h2', 'h3', 'p', 'ul', 'ol']):
                if element.name in ['h2', 'h3']:
                    # Save previous section
                    if current_section["content"].strip():
                        sections.append(current_section)
                    
                    # Start new section
                    header_text = element.get_text().strip()
                    # Remove [edit] links
                    header_text = re.sub(r'\[edit\]', '', header_text).strip()
                    current_section = {"title": header_text, "content": ""}
                
                elif element.name == 'p':
                    # Add paragraph content
                    para_text = element.get_text().strip()
                    if para_text and len(para_text) > 20:  # Skip very short paragraphs
                        current_section["content"] += para_text + "\n\n"
                
                elif element.name in ['ul', 'ol']:
                    # Add list content
                    list_items = element.find_all('li')
                    if list_items:
                        current_section["content"] += "\nKey points:\n"
                        for li in list_items:
                            item_text = li.get_text().strip()
                            if item_text:
                                current_section["content"] += f"• {item_text}\n"
                        current_section["content"] += "\n"
            
            # Add last section
            if current_section["content"].strip():
                sections.append(current_section)
            
            # Extract info box data
            infobox = soup.find('table', class_='infobox')
            infobox_data = {}
            if infobox:
                rows = infobox.find_all('tr')
                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) == 2:
                        key = cells[0].get_text().strip()
                        value = cells[1].get_text().strip()
                        infobox_data[key] = value
            
            print(f"✅ Scraped {len(sections)} sections from {title}")
            
            return {
                "title": title,
                "url": url,
                "sections": sections,
                "infobox": infobox_data,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize scraped text"""
        # Remove citations [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\"\']+', ' ', text)
        
        return text.strip()

class HealthDataRAG:
    """RAG system specialized for health data"""
    
    def __init__(self):
        self.scraper = HealthDataScraper()
        self.chroma_client = chromadb.PersistentClient(path="./health_rag_db")
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Create specialized collection for health data
        self.collection = self.chroma_client.get_or_create_collection(
            name="health_data_knowledge",
            metadata={"description": "Health data information from Wikipedia and other sources"}
        )
    
    def ingest_health_data(self, url: str):
        """Scrape and ingest health data into RAG system"""
        print("🏥 HEALTH DATA RAG INGESTION")
        print("=" * 40)
        
        # Scrape the data
        scraped_data = self.scraper.scrape_wikipedia_health_data(url)
        
        if not scraped_data:
            print("❌ Failed to scrape health data")
            return False
        
        # Prepare documents for ingestion
        documents = []
        metadatas = []
        ids = []
        
        # Process each section
        for i, section in enumerate(scraped_data["sections"]):
            if len(section["content"].strip()) < 100:  # Skip very short sections
                continue
            
            # Clean the content
            clean_content = self.scraper.clean_text(section["content"])
            
            # Create document
            doc_content = f"Section: {section['title']}\n\nContent: {clean_content}"
            
            documents.append(doc_content)
            metadatas.append({
                "source": "wikipedia_health_data",
                "url": scraped_data["url"],
                "section_title": section["title"],
                "page_title": scraped_data["title"],
                "scraped_at": scraped_data["scraped_at"],
                "content_type": "health_information",
                "word_count": len(clean_content.split())
            })
            ids.append(f"health_section_{i}")
        
        # Add infobox as a separate document if available
        if scraped_data["infobox"]:
            infobox_content = "Key Information:\n"
            for key, value in scraped_data["infobox"].items():
                infobox_content += f"{key}: {value}\n"
            
            documents.append(infobox_content)
            metadatas.append({
                "source": "wikipedia_health_data",
                "url": scraped_data["url"],
                "section_title": "Key Information",
                "page_title": scraped_data["title"],
                "scraped_at": scraped_data["scraped_at"],
                "content_type": "health_summary",
                "word_count": len(infobox_content.split())
            })
            ids.append("health_infobox")
        
        # Add to ChromaDB
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ Ingested {len(documents)} health data sections")
            print(f"📊 Total words processed: {sum(meta['word_count'] for meta in metadatas)}")
            
            # Show sample sections
            print(f"\n📚 Sample sections ingested:")
            for i, meta in enumerate(metadatas[:5]):
                print(f"   {i+1}. {meta['section_title']} ({meta['word_count']} words)")
            
            return True
        
        return False
    
    def query_health_data(self, question: str, n_results: int = 3) -> Dict:
        """Query health data with RAG"""
        print(f"\n🔍 Health Data Query: {question}")
        print("-" * 50)
        
        # Search for relevant documents
        search_results = self.collection.query(
            query_texts=[question],
            n_results=n_results
        )
        
        if not search_results['documents'][0]:
            return {
                "question": question,
                "answer": "No relevant health data found for this question.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Display search results
        documents = search_results['documents'][0]
        distances = search_results['distances'][0]
        metadatas = search_results['metadatas'][0]
        
        print(f"📄 Found {len(documents)} relevant sections:")
        for i, (doc, distance, meta) in enumerate(zip(documents, distances, metadatas)):
            similarity = 1.0 - (distance / 2.0)
            print(f"   {i+1}. {meta['section_title']} (similarity: {similarity:.3f})")
            print(f"      Preview: {doc[:100]}...")
        
        # Create context for OpenAI
        context = "\n\n".join([
            f"Section {i+1} - {meta['section_title']}:\n{doc}"
            for i, (doc, meta) in enumerate(zip(documents, metadatas))
        ])
        
        # Generate comprehensive answer
        system_prompt = """You are a knowledgeable health informatics expert. Use the provided health data information to answer questions accurately and comprehensively.

Guidelines:
- Focus on evidence-based information from the provided context
- Explain complex health data concepts clearly
- Mention data sources and reliability when relevant
- If information is incomplete, acknowledge limitations
- Provide practical insights when appropriate
- Use clear, professional language suitable for various audiences"""
        
        user_prompt = f"""Based on the following health data information, please provide a comprehensive answer to this question:

Question: {question}

Health Data Context:
{context}

Please provide a detailed, evidence-based answer using the health data information provided."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=600,
                temperature=0.6
            )
            
            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Calculate confidence based on similarity scores
            avg_similarity = sum(1.0 - (d / 2.0) for d in distances) / len(distances)
            confidence = min(avg_similarity * 0.9 + 0.1, 1.0)
            
            print(f"\n🤖 AI-POWERED HEALTH DATA ANSWER:")
            print("-" * 35)
            print(answer)
            print(f"\n📊 Analysis:")
            print(f"   • Tokens used: {tokens_used}")
            print(f"   • Confidence: {confidence:.3f}")
            print(f"   • Sources: {len(documents)} sections")
            
            return {
                "question": question,
                "answer": answer,
                "sources": [
                    {
                        "section": meta['section_title'],
                        "similarity": 1.0 - (dist / 2.0),
                        "content_preview": doc[:200] + "..."
                    }
                    for doc, dist, meta in zip(documents, distances, metadatas)
                ],
                "confidence": confidence,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return {
                "question": question,
                "answer": f"Error generating answer: {e}",
                "sources": [],
                "confidence": 0.0
            }

def main():
    """Main demonstration"""
    print("🏥 HEALTH DATA RAG SYSTEM")
    print("="*50)
    print("Scraping Wikipedia Health Data page and creating specialized RAG system")
    
    # Initialize RAG system
    health_rag = HealthDataRAG()
    
    # Target URL
    health_data_url = "https://en.wikipedia.org/wiki/Health_data"
    
    # Ingest health data
    print(f"\n🌐 Target URL: {health_data_url}")
    success = health_rag.ingest_health_data(health_data_url)
    
    if not success:
        print("❌ Failed to ingest health data")
        return
    
    # Test queries specific to health data
    health_queries = [
        "What is health data and why is it important?",
        "What are the main types of health data?",
        "How is health data used in healthcare systems?",
        "What are the privacy concerns with health data?",
        "How is electronic health records different from other health data?",
        "What role does health data play in public health?",
        "What are the challenges in health data management?",
        "How is health data used in medical research?"
    ]
    
    print(f"\n🧠 TESTING HEALTH DATA RAG QUERIES")
    print("="*45)
    
    results = []
    for i, query in enumerate(health_queries, 1):
        print(f"\n{'='*60}")
        print(f"QUERY {i}/{len(health_queries)}")
        print('='*60)
        
        result = health_rag.query_health_data(query)
        results.append(result)
        
        # Brief pause between queries
        time.sleep(1)
    
    # Summary
    print(f"\n\n📊 HEALTH DATA RAG SUMMARY")
    print("="*40)
    
    successful_queries = [r for r in results if r['confidence'] > 0.5]
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    total_tokens = sum(r.get('tokens_used', 0) for r in results)
    
    print(f"✅ Successful queries: {len(successful_queries)}/{len(results)}")
    print(f"📈 Average confidence: {avg_confidence:.3f}")
    print(f"🔢 Total tokens used: {total_tokens}")
    print(f"💾 Health data sections in database: {health_rag.collection.count()}")
    
    print(f"\n🎯 Best performing queries:")
    top_queries = sorted(results, key=lambda x: x['confidence'], reverse=True)[:3]
    for i, query in enumerate(top_queries, 1):
        print(f"   {i}. {query['question'][:60]}... (confidence: {query['confidence']:.3f})")
    
    print(f"\n✨ Your Health Data RAG system is ready!")
    print("🔍 You can now query comprehensive health data information")
    print("📚 Database contains Wikipedia health data knowledge")
    print("🤖 OpenAI provides intelligent, context-aware answers")

if __name__ == "__main__":
    main()