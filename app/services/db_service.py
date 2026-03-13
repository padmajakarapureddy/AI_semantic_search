from pymongo import MongoClient
from py2neo import Graph, Node as NeoNode, Relationship as NeoRel
from tinydb import TinyDB, Query
import networkx as nx
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.use_lite = False
        self.local_db = TinyDB("app/data/local_db.json")
        self.nx_graph = nx.MultiDiGraph()
        
        # Load existing graph if exists
        if os.path.exists("app/data/graph.json"):
            try:
                with open("app/data/graph.json", "r") as f:
                    data = json.load(f)
                    # Support both standard and link formats
                    if "links" in data:
                        self.nx_graph = nx.node_link_graph(data, edges='links')
                    else:
                        self.nx_graph = nx.node_link_graph(data)
                    logger.info(f"Loaded graph with {len(self.nx_graph.nodes)} nodes")
            except Exception as e:
                logger.error(f"Failed to load graph: {e}")
                self.nx_graph = nx.MultiDiGraph()

        # MongoDB Config
        try:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            self.mongo_client.server_info() 
            self.db = self.mongo_client["semantic_search_db"]
            self.docs_collection = self.db["documents"]
            logger.info("Connected to MongoDB")
        except Exception:
            logger.warning("MongoDB not available, using TinyDB fallback")
            self.use_lite = True

        # Neo4j Config
        try:
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            self.graph = Graph(neo4j_uri, auth=("neo4j", "password123"))
            self.graph.run("MATCH (n) RETURN n LIMIT 1") 
            logger.info("Connected to Neo4j")
        except Exception:
            logger.warning("Neo4j not available, using NetworkX fallback")
            self.use_lite = True

    def save_document(self, doc_id, content, metadata=None):
        doc = {
            "doc_id": doc_id,
            "content": content,
            "metadata": metadata or {}
        }
        
        if not self.use_lite:
            try:
                self.docs_collection.update_one({"doc_id": doc_id}, {"$set": doc}, upsert=True)
                doc_node = NeoNode("Document", doc_id=doc_id, content=content[:100] + "...")
                self.graph.merge(doc_node, "Document", "doc_id")
            except Exception as e:
                logger.error(f"Error saving to DB: {e}")
                self._save_lite(doc_id, doc, content)
        else:
            self._save_lite(doc_id, doc, content)
            
        return doc_id

    def _save_lite(self, doc_id, doc, content):
        Q = Query()
        self.local_db.upsert(doc, Q.doc_id == doc_id)
        self.nx_graph.add_node(doc_id, type="Document", content=content[:100])
        self._persist_nx()

    def add_relationship(self, doc_id, entity_name, rel_type="CONTAINS"):
        if not self.use_lite:
            try:
                doc_node = self.graph.nodes.match("Document", doc_id=doc_id).first()
                entity_node = NeoNode("Entity", name=entity_name)
                self.graph.merge(entity_node, "Entity", "name")
                rel = NeoRel(doc_node, rel_type, entity_node)
                self.graph.merge(rel)
            except Exception:
                self._add_rel_lite(doc_id, entity_name, rel_type)
        else:
            self._add_rel_lite(doc_id, entity_name, rel_type)

    def _add_rel_lite(self, doc_id, entity_name, rel_type):
        self.nx_graph.add_node(entity_name, type="Entity")
        self.nx_graph.add_edge(doc_id, entity_name, type=rel_type)
        self._persist_nx()

    def get_related_entities(self, doc_id):
        if not self.use_lite:
            try:
                query = f"""
                MATCH (d:Document {{doc_id: '{doc_id}'}})-[:CONTAINS]->(e:Entity)
                RETURN e.name as entity
                """
                results = self.graph.run(query).data()
                return [r['entity'] for r in results]
            except Exception:
                return self._get_entities_lite(doc_id)
        else:
            return self._get_entities_lite(doc_id)

    def _get_entities_lite(self, doc_id):
        if doc_id in self.nx_graph:
            return [n for n in self.nx_graph.neighbors(doc_id) if self.nx_graph.nodes[n].get("type") == "Entity"]
        return []

    def get_related_documents(self, doc_id):
        """
        Contextual Graph Traversal: Find documents that share entities with this doc.
        """
        if not self.use_lite:
            try:
                query = f"""
                MATCH (d:Document {{doc_id: '{doc_id}'}})-[:CONTAINS]->(e:Entity)<-[:CONTAINS]-(other:Document)
                WHERE other.doc_id <> d.doc_id
                RETURN DISTINCT other.doc_id as doc_id
                """
                results = self.graph.run(query).data()
                return [r['doc_id'] for r in results]
            except Exception:
                return self._get_related_docs_lite(doc_id)
        else:
            return self._get_related_docs_lite(doc_id)

    def _get_related_docs_lite(self, doc_id):
        related_docs = set()
        if doc_id in self.nx_graph:
            entities = [n for n in self.nx_graph.neighbors(doc_id) if self.nx_graph.nodes[n].get("type") == "Entity"]
            for entity in entities:
                # Find other docs that connect to this entity
                for other_doc in self.nx_graph.predecessors(entity):
                    if other_doc != doc_id and self.nx_graph.nodes[other_doc].get("type") == "Document":
                        related_docs.add(other_doc)
        return list(related_docs)

    def get_all_documents(self):
        if not self.use_lite:
            try:
                return list(self.docs_collection.find({}, {"_id": 0}))
            except Exception:
                return self.local_db.all()
        else:
            return self.local_db.all()

    def _persist_nx(self):
        data = nx.node_link_data(self.nx_graph, edges='links')
        with open("app/data/graph.json", "w") as f:
            json.dump(data, f)
            
    def get_full_graph(self):
        """Return graph data for visualization"""
        return nx.node_link_data(self.nx_graph, edges='links')

    def close(self):
        """Release database handles"""
        try:
            if hasattr(self, 'local_db'):
                self.local_db.close()
            logger.info("Database handles closed.")
        except Exception as e:
            logger.error(f"Error closing database handles: {e}")
