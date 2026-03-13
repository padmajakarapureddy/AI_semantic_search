from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import os
import hashlib

class BaseConnector(ABC):
    @abstractmethod
    def list_files(self) -> List[Dict]:
        """List all files available in the source"""
        pass

    @abstractmethod
    def get_file_content(self, file_id: str) -> str:
        """Get the text content of a specific file"""
        pass

    def get_file_hash(self, content: str) -> str:
        return hashlib.md5(content.encode('utf-8')).hexdigest()
