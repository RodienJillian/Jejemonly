from typing import List, Tuple
from .edit_distance import EditDistance

class FuzzyMatcher:
    """Finds similar words."""
    
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
        self.edit_distance = EditDistance()
    
    def find_best_match(self, word: str, candidates: List[str]) -> Tuple[str, float]:
        """Find the best matching word from list."""
        best_match = ""
        best_score = 0.0
        
        for candidate in candidates:
            score = self.edit_distance.similarity(word, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate
        
        return best_match, best_score
    
    def find_matches_above_threshold(self, word: str, candidates: List[str]) -> List[Tuple[str, float]]:
        matches = []
        for candidate in candidates:
            score = self.edit_distance.similarity(word, candidate)
            if score >= self.threshold:
                matches.append((candidate, score))
        
        return sorted(matches, key=lambda x: x[1], reverse=True)