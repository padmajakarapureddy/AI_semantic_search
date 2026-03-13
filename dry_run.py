import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:8000/api"

# 1. Manual Docs for initial setup
docs = [
    {
        "doc_id": "ai_primer",
        "content": "Artificial Intelligence is the simulation of human intelligence by machines."
    }
]

def dry_run():
    print("=== UNIVERSAL SEARCH DRY RUN ===")
    
    # 1. Manual Ingest with Auto-Extraction
    print("\n[Step 1] Manual Ingest + Auto-NER")
    for doc in docs:
        resp = requests.post(f"{BASE_URL}/ingest", json=doc)
        if resp.status_code == 200:
            data = resp.json()
            print(f"-> Ingested: {doc['doc_id']}")
            print(f"   Entities Extracted: {data.get('extracted_entities')}")
    
    # 2. Connector Ingest (Phase 3)
    print("\n[Step 2] Universal Connector (Local Sync)")
    # We will sync the 'app/core' directory of THIS project
    sync_path = os.path.abspath("app/core")
    print(f"-> Syncing local directory: {sync_path}")
    
    resp = requests.post(f"{BASE_URL}/connectors/add", json={"type": "local", "path": sync_path})
    if resp.status_code == 200:
        print("-> Sync Request Sent Successfully.")
        print("   Waiting for background crawler (3s)...")
        time.sleep(3)
    else:
        print(f"-> Sync Error: {resp.text}")

    # 3. Test Semantic Search (Phase 2)
    # The term 'transformer' is in vectorizer.py (which was synced in Step 2)
    # The term 'thinking' is conceptually similar to doc1 (ai_primer)
    queries = [
        "thinking machines",          # Should match 'Artificial Intelligence'
        "neural embedding logic"      # Should match 'vectorizer.py' or similar from sync
    ]

    print("\n[Step 3] Neural Semantic Queries")
    for q in queries:
        print(f"\nQuery: '{q}'")
        resp = requests.post(f"{BASE_URL}/search", json={"query": q, "top_k": 2})
        results = resp.json().get("results", [])
        if not results:
            print("   -> No matches found.")
        for r in results:
            doc_display = r['doc_id'].split(os.sep)[-1] # Show filename for clarity
            print(f"   -> Result: {doc_display} (Score: {r['score']:.4f})")
            print(f"      Context: {r['content'][:150]}...")
            print(f"      Matched Entities: {r.get('entities', [])}")
            if r.get('related_docs'):
                print(f"      Graph Connections: {[d.split(os.sep)[-1] for d in r['related_docs']]}")

    print("\n=== Dry Run Complete ===")

if __name__ == "__main__":
    dry_run()
