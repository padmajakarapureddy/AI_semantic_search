import requests
import time
import os

BASE_URL = "http://127.0.0.1:8000/api"

def log_test(step, message):
    print(f"\n[Step {step}] {message}")

def run_comprehensive_test():
    print("=== DEEP WIPE & MULTI-PATH VERIFICATION ===")

    # Step 1: Wipe everything
    log_test(1, "Wiping database and clearing all state...")
    resp = requests.delete(f"{BASE_URL}/ingest")
    print(f"-> Response: {resp.json()}")

    # Step 2: Verify it's empty
    log_test(2, "Verifying empty state search...")
    resp = requests.post(f"{BASE_URL}/search", json={"query": "anything", "top_k": 1})
    results = resp.json().get("results", [])
    print(f"-> Results found: {len(results)} (Expected: 0)")

    # Step 3: Ingest Data Set A (Artificial Intelligence)
    log_test(3, "Ingesting Data Set A (Artificial Intelligence)...")
    requests.post(f"{BASE_URL}/ingest", json={
        "doc_id": "test_ai",
        "content": "Artificial Intelligence involves machines that can perform human tasks."
    })
    
    # Step 4: Verify Search matches Set A
    log_test(4, "Searching for Set A...")
    resp = requests.post(f"{BASE_URL}/search", json={"query": "human tasks", "top_k": 1})
    results = resp.json().get("results", [])
    if results:
        print(f"-> Found: {results[0]['doc_id']} (Score: {results[0]['score']:.4f})")
    else:
        print("-> ALERT: Search failed for Set A")

    # Step 5: Perform the DEEP WIPE (Crucial Test)
    log_test(5, "Performing DEEP WIPE before switching to Data Set B...")
    requests.delete(f"{BASE_URL}/ingest")
    time.sleep(1) # Tiny pause for file locks

    # Step 6: Ingest Data Set B (College/Institute - Different Topic)
    log_test(6, "Syncing Data Set B (Simulated Path Indexing)...")
    # Instead of full connector, we'll use ingest to simulate different drive data
    requests.post(f"{BASE_URL}/ingest", json={
        "doc_id": "college_details",
        "content": "The Institute of Higher Learning provides advanced education and college degrees."
    })

    # Step 7: The ULTIMATE Test - Semantic Isolation
    log_test(7, "Verification: Searching for 'Institute' (Should ONLY find College, NOT AI)...")
    resp = requests.post(f"{BASE_URL}/search", json={"query": "Institute", "top_k": 5})
    results = resp.json().get("results", [])
    
    found_ai = False
    found_college = False
    
    for r in results:
        doc_id = r['doc_id']
        print(f"-> Found result: {doc_id} (Score: {r['score']:.4f})")
        if "ai" in doc_id: found_ai = True
        if "college" in doc_id: found_college = True

    if found_college and not found_ai:
        print("\n✅ SUCCESS: Only the NEW path data is visible. Wipe worked perfectly.")
    elif found_ai:
        print("\n❌ FAILED: Old 'AI' data is still appearing in results!")
    else:
        print("\n⚠️ UNKNOWN: No relevant results found.")

    print("\n=== Comprehensive Test Complete ===")

if __name__ == "__main__":
    run_comprehensive_test()
