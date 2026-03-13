import spacy
import logging

logger = logging.getLogger(__name__)

class NLPEngine:
    def __init__(self, model_name="en_core_web_sm"):
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except Exception as e:
            logger.warning(f"Could not load spaCy model {model_name}: {e}")
            self.nlp = None

    def extract_entities(self, content: str):
        if not self.nlp:
            return []
        
        doc = self.nlp(content)
        entities = list(set([ent.text for ent in doc.ents if ent.label_ in ["ORG", "PERSON", "GPE", "PRODUCT", "TECHNOLOGY"]]))
        
        # Fallback to Important Nouns if no named entities found
        if not entities:
            entities = [token.text for token in doc if token.pos_ in ["PROPN", "NOUN"]][:3]
        
        return entities
