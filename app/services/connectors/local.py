from app.services.connectors.base import BaseConnector
import os
from typing import List, Dict

class LocalConnector(BaseConnector):
    def __init__(self, root_path: str, exclude_dirs: List[str] = None):
        self.root_path = root_path
        self.exclude_dirs = exclude_dirs or ['venv', '__pycache__', '.git', 'node_modules', '.gemini']

    def list_files(self) -> List[Dict]:
        files = []
        for root, dirs, filenames in os.walk(self.root_path):
            # Optimizing search: don't descend into excluded dirs
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for filename in filenames:
                if filename.endswith(('.txt', '.md', '.py', '.html', '.css', '.js')):
                    full_path = os.path.join(root, filename)
                    files.append({
                        "file_id": full_path,
                        "name": filename,
                        "source": "local"
                    })
        return files

    def get_file_content(self, file_id: str) -> str:
        try:
            with open(file_id, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {file_id}: {str(e)}"
