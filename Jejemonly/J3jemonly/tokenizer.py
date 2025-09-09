import re
from typing import List

class Tokenizer:
    def __init__(self):
        self.word_pattern = re.compile(r'\b[\w@#$+!\']+\b')
        
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        return self.word_pattern.findall(text.lower())
    
    def detokenize(self, tokens: List[str]) -> str:
        """Join tokens back into text."""
        return ' '.join(tokens)