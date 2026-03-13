from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np
import pickle
import os

class SemanticSearchEngine:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.document_embeddings = None
        self.doc_ids = []
        self.documents = []

    def fit(self, documents, doc_ids):
        if not documents:
            self.documents = []
            self.doc_ids = []
            self.document_embeddings = None
            return
        self.documents = documents
        self.doc_ids = doc_ids
        self.document_embeddings = self.model.encode(documents, convert_to_tensor=True)

    def search(self, query, top_k=5):
        if self.document_embeddings is None:
            return []
        
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        cos_scores = util.cos_sim(query_embedding, self.document_embeddings)[0]
        
        # Sort scores and get top-k
        top_results = torch.topk(cos_scores, k=min(top_k, len(cos_scores)))
        
        results = []
        for score, idx in zip(top_results[0], top_results[1]):
            results.append({
                "doc_id": self.doc_ids[idx],
                "score": float(score),
                "content": self.documents[idx]
            })
        return results

    def save(self, path="app/data/semantic_vectorizer.pkl"):
        # We don't save the full model, just the embeddings and document info
        with open(path, 'wb') as f:
            pickle.dump({
                "embeddings": self.document_embeddings.cpu() if self.document_embeddings is not None else None,
                "documents": self.documents,
                "doc_ids": self.doc_ids
            }, f)

    def load(self, path="app/data/semantic_vectorizer.pkl"):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = pickle.load(f)
                if data["embeddings"] is not None:
                    self.document_embeddings = torch.tensor(data["embeddings"])
                self.documents = data["documents"]
                self.doc_ids = data["doc_ids"]
