import logging
import time
from typing import List
from app.services.connectors.local import LocalConnector
from app.services.db_service import DatabaseService
from app.core.vectorizer import SemanticSearchEngine
from app.core.nlp import NLPEngine

logger = logging.getLogger(__name__)

class CrawlerService:
    def __init__(self, db_service: DatabaseService, search_engine: SemanticSearchEngine):
        self.db_service = db_service
        self.search_engine = search_engine
        self.nlp_engine = NLPEngine()
        self.connectors = []
        self.indexed_hashes = {} # file_id -> hash

    def reset(self):
        self.connectors = []
        self.indexed_hashes = {}
        logger.info("Crawler service reset.")

    def add_connector(self, connector):
        self.connectors.append(connector)

    def sync_all(self):
        logger.info("Starting universal sync...")
        for connector in self.connectors:
            files = connector.list_files()
            for file_info in files:
                file_id = file_info["file_id"]
                content = connector.get_file_content(file_id)
                content_hash = connector.get_file_hash(content)

                # Only index if content changed
                if self.indexed_hashes.get(file_id) != content_hash:
                    logger.info(f"Indexing/Updating: {file_info['name']}")
                    self._ingest_file(file_info["file_id"], content)
                    self.indexed_hashes[file_id] = content_hash
        
        # After indexing all, refit search engine
        all_docs = self.db_service.get_all_documents()
        if all_docs:
            self.search_engine.fit([d['content'] for d in all_docs], [d['doc_id'] for d in all_docs])
            self.search_engine.save()

    def _ingest_file(self, doc_id, content):
        metadata = {"source_type": "managed_connector"}
        self.db_service.save_document(doc_id, content, metadata)
        
        # Automatic Entity Extraction
        entities = self.nlp_engine.extract_entities(content)
        if entities:
            for entity in entities:
                self.db_service.add_relationship(doc_id, entity)
