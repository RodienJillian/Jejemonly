import re

class TextPreprocessor:
    """Handles removing punctuation and special characters."""
    
    def __init__(self):
        self.punctuation_pattern = re.compile(r'[^\w\s]')
        self.special_chars_pattern = re.compile(r'[^a-zA-Z0-9\s]')
        self.multiple_spaces_pattern = re.compile(r'\s+')
        
    def remove_punctuation(self, text: str) -> str:
        """Remove punctuation from text."""
        return self.punctuation_pattern.sub('', text)
    
    def remove_special_characters(self, text: str) -> str:
        """Remove special characters from text."""
        return self.special_chars_pattern.sub('', text)
    
    def normalize_spaces(self, text: str) -> str:
        """Normalize multiple spaces to single space."""
        return self.multiple_spaces_pattern.sub(' ', text).strip()
    
    def preprocess(self, text: str) -> str:
        text = self.remove_punctuation(text)
        text = self.remove_special_characters(text)
        text = self.normalize_spaces(text)
        return text.lower()