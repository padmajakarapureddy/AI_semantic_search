# AI-Powered Semantic Search with Knowledge Graph

A high-performance semantic document search engine that combines vector-based retrieval with graph-based entity relationships.

## 🚀 Features

- **Semantic Search**: Context-aware document retrieval using `all-MiniLM-L6-v2` Sentence Transformers.
- **Knowledge Graph Integration**: Automatic entity extraction (Organizations, People, Locations) using spaCy, linked via a Knowledge Graph.
- **Hybrid Storage Architecture**: 
  - **Production Mode**: MongoDB for document storage and Neo4j for graph relationships.
  - **Lite Mode**: Local JSON storage (TinyDB) and memory-based graphs (NetworkX) for zero-config local runs.
- **Automated Ingestion**: Local directory connector to sync and index local files automatically.
- **Modern Backend**: FastAPI-powered REST implementation with background task support.

## 🛠️ Project Structure

- `app/api`: REST API endpoints and routing logic.
- `app/core`: Core engines for semantic vectorization and NLP.
- `app/services`: Business logic for database management, crawling, and connectors.
- `app/static`: (WIP) Frontend interface assets.
- `docker-compose.yml`: Container orchestration for MongoDB and Neo4j.

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.8+
- Docker & Docker Compose (for production databases)

### 2. Install Dependencies
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 3. Spin up Databases (Optional)
```bash
docker-compose up -d
```

### 4. Run the Application
```bash
uvicorn app.main:app --reload
```

## 🔌 API Endpoints

- `POST /api/ingest`: Manually ingest a document for indexing.
- `POST /api/search`: Perform a semantic search query.
- `POST /api/connectors/add`: Add a local directory to sync and monitor.
- `GET /api/graph`: Retrieve the full knowledge graph structure.
