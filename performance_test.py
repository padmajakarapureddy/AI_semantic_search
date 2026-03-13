import requests
import time
import os

BASE_URL = "http://127.0.0.1:8000/api"

def benchmark():
    print("=== SEMANTIC SEARCH EFFICIENCY TEST ===")
    
    # 1. Ingest test documentation if needed
    # doc = {
    #     "doc_id": "efficiency_test_doc",
    #     "content": "The efficiency of a semantic search system is measured by its latency, recall, and the depth of its knowledge graph connections."
    # }
    # requests.post(f"{BASE_URL}/ingest", json=doc)
    
    # 2. Performance Benchmarking for Search
    queries = [
        "measurement of search quality",
        "how does the graph connect documents?",
        "neural processing speed"
    ]
    
    print(f"\n{'Query':<40} | {'Latency':<10} | {'Top Match':<20}")
    print("-" * 75)
    
    for q in queries:
        start_time = time.time()
        resp = requests.post(f"{BASE_URL}/search", json={"query": q, "top_k": 3})
        end_time = time.time()
        
        latency = (end_time - start_time) * 1000 # ms
        results = resp.json().get("results", [])
        
        top_match = results[0]['doc_id'].split(os.sep)[-1] if results else "No Match"
        
        print(f"{q:<40} | {latency:>7.2f} ms | {top_match:<20}")
        
        if results:
            print(f"   -> Top Content Snippet: {results[0]['content'][:80]}...")
            print(f"   -> Entities Found: {results[0].get('entities', [])}")
            print(f"   -> Graph Links: {len(results[0].get('related_docs', []))} connections")
            print()

if __name__ == "__main__":
    benchmark()
