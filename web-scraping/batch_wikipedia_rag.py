#!/usr/bin/env python3
"""
Batch Wikipedia RAG Processor
Add multiple Wikipedia pages to your RAG system at once
"""
import os
import sys
import time
import json
from pathlib import Path
from typing import List, Dict
from urllib.parse import urlparse

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from wikipedia_rag_scraper import WikipediaRAGIntegrator
from dotenv import load_dotenv

load_dotenv()

class BatchWikipediaProcessor:
    """Batch processor for multiple Wikipedia pages"""
    
    def __init__(self, collection_name: str = "batch_wiki_knowledge"):
        self.integrator = WikipediaRAGIntegrator(collection_name)
        self.results = []
    
    def process_urls_from_file(self, file_path: str) -> Dict:
        """Process URLs from a text file (one URL per line)"""
        print(f"📂 Processing URLs from file: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return {"success": False, "error": "File not found"}
        
        try:
            with open(file_path, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            return self.process_url_list(urls, f"file: {file_path}")
            
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return {"success": False, "error": str(e)}
    
    def process_url_list(self, urls: List[str], source: str = "manual list") -> Dict:
        """Process a list of Wikipedia URLs"""
        print(f"\n🚀 BATCH WIKIPEDIA PROCESSING")
        print("="*45)
        print(f"Source: {source}")
        print(f"URLs to process: {len(urls)}")
        print("-" * 45)
        
        successful = 0
        failed = 0
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Processing: {url}")
            
            # Validate URL
            if not self._is_valid_wikipedia_url(url):
                print(f"❌ Invalid Wikipedia URL: {url}")
                results.append({
                    "url": url,
                    "success": False,
                    "error": "Invalid Wikipedia URL",
                    "processing_time": 0
                })
                failed += 1
                continue
            
            # Process URL
            start_time = time.time()
            
            try:
                success = self.integrator.add_wikipedia_page(url)
                processing_time = time.time() - start_time
                
                if success:
                    successful += 1
                    results.append({
                        "url": url,
                        "success": True,
                        "error": None,
                        "processing_time": processing_time
                    })
                    print(f"✅ Successfully processed ({processing_time:.2f}s)")
                else:
                    failed += 1
                    results.append({
                        "url": url,
                        "success": False,
                        "error": "Processing failed",
                        "processing_time": processing_time
                    })
                    print(f"❌ Processing failed ({processing_time:.2f}s)")
                
                # Brief pause between requests to be respectful
                time.sleep(1)
                
            except Exception as e:
                processing_time = time.time() - start_time
                failed += 1
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e),
                    "processing_time": processing_time
                })
                print(f"❌ Error: {e} ({processing_time:.2f}s)")
        
        # Summary
        total_time = sum(r['processing_time'] for r in results)
        
        print(f"\n📊 BATCH PROCESSING SUMMARY")
        print("="*35)
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Total time: {total_time:.2f} seconds")
        print(f"📊 Average time per page: {total_time/len(urls):.2f}s")
        print(f"💾 Total documents in collection: {self.integrator.collection.count()}")
        
        return {
            "success": True,
            "total_urls": len(urls),
            "successful": successful,
            "failed": failed,
            "results": results,
            "total_time": total_time,
            "collection_size": self.integrator.collection.count()
        }
    
    def _is_valid_wikipedia_url(self, url: str) -> bool:
        """Check if URL is a valid Wikipedia page"""
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ['http', 'https'] and
                'wikipedia.org' in parsed.netloc and
                '/wiki/' in parsed.path
            )
        except:
            return False
    
    def save_results(self, results: Dict, output_file: str):
        """Save processing results to a JSON file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Results saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")
    
    def create_sample_urls_file(self, file_path: str):
        """Create a sample URLs file for demonstration"""
        sample_urls = [
            "# Sample Wikipedia URLs for Health & Technology Topics",
            "# Remove the # at the start of lines to include them",
            "",
            "https://en.wikipedia.org/wiki/Health_data",
            "https://en.wikipedia.org/wiki/Electronic_health_record",
            "https://en.wikipedia.org/wiki/Health_informatics",
            "https://en.wikipedia.org/wiki/Medical_device",
            "https://en.wikipedia.org/wiki/Artificial_intelligence_in_healthcare",
            "https://en.wikipedia.org/wiki/Telemedicine",
            "https://en.wikipedia.org/wiki/Digital_health",
            "https://en.wikipedia.org/wiki/Health_Insurance_Portability_and_Accountability_Act",
            "",
            "# Add your own Wikipedia URLs below:",
            "# https://en.wikipedia.org/wiki/Your_Topic_Here"
        ]
        
        try:
            with open(file_path, 'w') as f:
                f.write('\n'.join(sample_urls))
            print(f"📄 Sample URLs file created: {file_path}")
            print("   Edit this file and remove # from URLs you want to process")
        except Exception as e:
            print(f"❌ Error creating sample file: {e}")

def main():
    """Main CLI interface"""
    processor = BatchWikipediaProcessor()
    
    if len(sys.argv) < 2:
        print("🌟 BATCH WIKIPEDIA RAG PROCESSOR")
        print("="*40)
        print("Usage:")
        print("  python batch_wikipedia_rag.py <urls_file>")
        print("  python batch_wikipedia_rag.py --create-sample [file]")
        print("  python batch_wikipedia_rag.py --health-demo")
        print("\nExamples:")
        print("  python batch_wikipedia_rag.py urls.txt")
        print("  python batch_wikipedia_rag.py --create-sample sample_urls.txt")
        print("  python batch_wikipedia_rag.py --health-demo")
        return
    
    arg = sys.argv[1]
    
    if arg == "--create-sample":
        sample_file = sys.argv[2] if len(sys.argv) > 2 else "sample_wikipedia_urls.txt"
        processor.create_sample_urls_file(sample_file)
        
    elif arg == "--health-demo":
        print("🏥 HEALTH-FOCUSED WIKIPEDIA RAG DEMO")
        print("="*45)
        
        health_urls = [
            "https://en.wikipedia.org/wiki/Health_data",
            "https://en.wikipedia.org/wiki/Electronic_health_record",
            "https://en.wikipedia.org/wiki/Health_informatics",
            "https://en.wikipedia.org/wiki/Digital_health"
        ]
        
        results = processor.process_url_list(health_urls, "health demo")
        
        if results["success"] and results["successful"] > 0:
            print(f"\n🧠 Testing knowledge with sample queries:")
            test_queries = [
                "What is the difference between health data and electronic health records?",
                "How does health informatics improve healthcare delivery?",
                "What are the main benefits of digital health technologies?"
            ]
            
            for i, query in enumerate(test_queries, 1):
                print(f"\n{'='*60}")
                print(f"TEST QUERY {i}: {query}")
                print('='*60)
                processor.integrator.query_wikipedia_knowledge(query)
                time.sleep(1)
        
        # Save results
        processor.save_results(results, "health_demo_results.json")
        
    else:
        # Process URLs from file
        if not os.path.exists(arg):
            print(f"❌ File not found: {arg}")
            return
        
        results = processor.process_urls_from_file(arg)
        
        if results.get("success"):
            # Save results
            output_file = f"batch_results_{int(time.time())}.json"
            processor.save_results(results, output_file)

if __name__ == "__main__":
    main()