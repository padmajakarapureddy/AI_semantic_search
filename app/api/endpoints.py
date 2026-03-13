from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from app.services.db_service import DatabaseService
from app.core.vectorizer import SemanticSearchEngine
from app.services.crawler import CrawlerService
from app.services.connectors.local import LocalConnector
import spacy
import logging
import os

from app.core.nlp import NLPEngine

logger = logging.getLogger(__name__)

router = APIRouter()
db_service = DatabaseService()
search_engine = SemanticSearchEngine()
crawler = CrawlerService(db_service, search_engine)
nlp_engine = NLPEngine()

# Initialize search engine
docs = db_service.get_all_documents()
if docs:
    search_engine.fit([d['content'] for d in docs], [d['doc_id'] for d in docs])

class DocumentIngest(BaseModel):
    doc_id: str
    content: str
    metadata: Optional[dict] = None
    entities: Optional[List[str]] = None

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5

class ConnectorConfig(BaseModel):
    type: str # 'local'
    path: str
    clear_on_add: bool = False

@router.post("/ingest")
async def ingest_document(doc: DocumentIngest):
    try:
        db_service.save_document(doc.doc_id, doc.content, doc.metadata)
        entities = doc.entities or nlp_engine.extract_entities(doc.content)
        if entities:
            for entity in entities:
                db_service.add_relationship(doc.doc_id, entity)
        
        all_docs = db_service.get_all_documents()
        search_engine.fit([d['content'] for d in all_docs], [d['doc_id'] for d in all_docs])
        search_engine.save()
        return {"status": "success", "doc_id": doc.doc_id, "extracted_entities": entities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/ingest")
async def clear_database():
    try:
        import os
        # Close database handles to release file locks
        db_service.close()
        
        # Explicitly remove files with error handling
        files = ["app/data/graph.json", "app/data/local_db.json", "app/data/semantic_vectorizer.pkl"]
        for f in files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                    logger.info(f"Removed: {f}")
                except Exception as ex:
                    logger.warning(f"Could not remove {f}: {ex}")

        # Re-initialize services with fresh state
        db_service.__init__() 
        search_engine.fit([], []) # Clear in-memory embeddings
        crawler.reset()
        
        return {"status": "databases deleted and services reset"}
    except Exception as e:
        logger.error(f"Wipe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_documents(query: SearchQuery):
    try:
        results = search_engine.search(query.query, query.top_k)
        for res in results:
            res["entities"] = db_service.get_related_entities(res["doc_id"])
            res["related_docs"] = db_service.get_related_documents(res["doc_id"])
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connectors/add")
async def add_connector(config: ConnectorConfig, background_tasks: BackgroundTasks):
    if config.type == 'local':
        if not os.path.exists(config.path):
            raise HTTPException(status_code=400, detail="Path does not exist")
        
        if config.clear_on_add:
            await clear_database()

        conn = LocalConnector(config.path)
        crawler.add_connector(conn)
        # Background sync to avoid frontend timeout
        background_tasks.add_task(crawler.sync_all)
        return {"status": "sync started in background", "path": config.path, "cleared": config.clear_on_add}
    
    return {"status": "unsupported connector type"}

@router.get("/graph")
async def get_graph():
    return db_service.get_full_graph()
