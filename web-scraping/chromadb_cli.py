#!/usr/bin/env python3
"""
ChromaDB Command Line Interface
Usage: python chromadb_cli.py [command] [options]
"""
import chromadb
import json
import sys
from typing import Optional

class ChromaCLI:
    def __init__(self, db_path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        print(f"📁 Connected to ChromaDB at: {db_path}")
    
    def list_collections(self):
        """List all collections"""
        collections = self.client.list_collections()
        print(f"\n📚 Collections ({len(collections)}):")
        for i, collection in enumerate(collections, 1):
            count = collection.count()
            print(f"  {i}. {collection.name} ({count} documents)")
    
    def show_collection(self, name: str):
        """Show collection details"""
        try:
            collection = self.client.get_collection(name)
            count = collection.count()
            print(f"\n📖 Collection: {name}")
            print(f"   Documents: {count}")
            
            if count > 0:
                # Get all data
                data = collection.get()
                print(f"   Sample documents:")
                for i, (doc, meta, doc_id) in enumerate(zip(
                    data['documents'][:3], 
                    data['metadatas'][:3], 
                    data['ids'][:3]
                )):
                    print(f"     {i+1}. ID: {doc_id}")
                    print(f"        Text: {doc[:100]}...")
                    print(f"        Meta: {meta}")
                    print()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def search_collection(self, name: str, query: str, n_results: int = 5):
        """Search in collection"""
        try:
            collection = self.client.get_collection(name)
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            print(f"\n🔍 Search results for '{query}' in '{name}':")
            if results['documents'][0]:
                for i, (doc, dist, meta, doc_id) in enumerate(zip(
                    results['documents'][0],
                    results['distances'][0],
                    results['metadatas'][0],
                    results['ids'][0]
                ), 1):
                    print(f"  {i}. Distance: {dist:.4f}")
                    print(f"     ID: {doc_id}")
                    print(f"     Text: {doc[:150]}...")
                    print(f"     Meta: {meta}")
                    print()
            else:
                print("   No results found")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def export_collection(self, name: str, output_file: str = None):
        """Export collection to JSON"""
        try:
            collection = self.client.get_collection(name)
            data = collection.get()
            
            export_data = {
                'collection_name': name,
                'count': len(data['documents']),
                'documents': []
            }
            
            for doc, meta, doc_id in zip(data['documents'], data['metadatas'], data['ids']):
                export_data['documents'].append({
                    'id': doc_id,
                    'text': doc,
                    'metadata': meta
                })
            
            output_file = output_file or f"{name}_export.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Exported {len(data['documents'])} documents to {output_file}")
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("ChromaDB CLI Usage:")
        print("  python chromadb_cli.py list                    - List all collections")
        print("  python chromadb_cli.py show <collection>       - Show collection details")
        print("  python chromadb_cli.py search <collection> <query> [n] - Search collection")
        print("  python chromadb_cli.py export <collection> [file] - Export to JSON")
        return
    
    cli = ChromaCLI()
    command = sys.argv[1].lower()
    
    if command == "list":
        cli.list_collections()
    
    elif command == "show" and len(sys.argv) > 2:
        cli.show_collection(sys.argv[2])
    
    elif command == "search" and len(sys.argv) > 3:
        collection_name = sys.argv[2]
        query = sys.argv[3]
        n_results = int(sys.argv[4]) if len(sys.argv) > 4 else 5
        cli.search_collection(collection_name, query, n_results)
    
    elif command == "export" and len(sys.argv) > 2:
        collection_name = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        cli.export_collection(collection_name, output_file)
    
    else:
        print("❌ Invalid command or missing arguments")

if __name__ == "__main__":
    main()