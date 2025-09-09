import re
from typing import Dict, List

class Lemmatizer:
    def __init__(self):
        self.prefix_rules = {
            'nag': ['nag', 'mag'],
            'naka': ['naka', 'maka'],
            'nai': ['nai', 'mai'],
            'napa': ['napa', 'mapa'],
            'naging': ['naging', 'maging'],
            'naki': ['naki', 'maki'],
            'nang': ['nang', 'mang'],
            'naka': ['naka', 'ka'],
            'nai': ['nai', 'i'],
            'na': ['na', 'ma']
        }
        
        self.suffix_rules = {
            'ing': '',
            'an': '',
            'in': '',
            'ng': '',
            'han': '',
            'hin': '',
            'on': '',
            'un': ''
        }
    
    def lemmatize(self, word: str) -> str:
        """lemmatization by removing common affixes."""
        original_word = word
        
        # Handle prefixes
        for prefix, alternatives in self.prefix_rules.items():
            if word.startswith(prefix):
                word = word[len(prefix):]
                break
        
        # Handle suffixes
        for suffix in self.suffix_rules:
            if word.endswith(suffix) and len(word) > len(suffix):
                word = word[:-len(suffix)]
                break
        
        if len(word) < 2:
            return original_word
        
        return word