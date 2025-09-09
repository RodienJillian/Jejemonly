import json
import re
from typing import Dict, List, Optional

class LexiconManager:
    def __init__(self, lexicon_file: str = './lexicon/dictionary.json', characters_file: str = './lexicon/characters.json', words_file: str = './lexicon/words.txt'):
        self.lexicon_file = lexicon_file
        self.characters_file = characters_file
        self.words_file = words_file
        self.lexicon = self.load_lexicon()
        self.characters = self.load_characters()
        self.letter_variants = self.characters.get('letter_variants', {})
        self.jejemon_to_normal = self.lexicon.get('jejemon_to_normal', {})
        self.common_replacements = self.lexicon.get('common_replacements', {})
        self.variant_to_letter = self._create_variant_to_letter()
        self.words_set = self.load_words_txt()

    def load_lexicon(self) -> Dict:
        try:
            with open(self.lexicon_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Lexicon file '{self.lexicon_file}' not found. Using empty lexicon.")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in lexicon file '{self.lexicon_file}': {e}")
            return {}

    def load_characters(self) -> Dict:
        try:
            with open(self.characters_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Characters file '{self.characters_file}' not found. Using empty characters.")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in characters file '{self.characters_file}': {e}")
            return {}

    def load_words_txt(self) -> set:
        words = set()
        try:
            with open(self.words_file, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word:
                        words.add(word)
        except FileNotFoundError:
            print(f"Warning: Words file '{self.words_file}' not found. Using empty set.")
        return words

    def is_in_words_txt(self, word: str) -> bool:
        return word.lower() in self.words_set

    def _create_variant_to_letter(self) -> Dict[str, str]:
        variant_map = {}
        for letter, variants in self.letter_variants.items():
            for variant in variants:
                variant_map[variant.lower()] = letter.lower()
        return variant_map

    def get_base_letter(self, variant: str) -> Optional[str]:
        return self.variant_to_letter.get(variant.lower())

    def get_variants(self, letter: str) -> List[str]:
        return self.letter_variants.get(letter.lower(), [])

    def get_all_variants(self) -> List[str]:
        all_variants = []
        for variants in self.letter_variants.values():
            all_variants.extend(variants)
        return all_variants

    def add_variant(self, letter: str, variant: str):
        letter = letter.lower()
        variant = variant.lower()
        if letter not in self.letter_variants:
            self.letter_variants[letter] = []
        if variant not in self.letter_variants[letter]:
            self.letter_variants[letter].append(variant)
            self.variant_to_letter[variant] = letter
        self.characters['letter_variants'] = self.letter_variants

    def save_lexicon(self):
        try:
            with open(self.lexicon_file, 'w', encoding='utf-8') as f:
                json.dump(self.lexicon, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving lexicon: {e}")

    def save_characters(self):
        try:
            with open(self.characters_file, 'w', encoding='utf-8') as f:
                json.dump(self.characters, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving characters: {e}")

    def save_all(self):
        """Save both lexicon and characters files"""
        self.save_lexicon()
        self.save_characters()

    def apply_character_replacements(self, word: str) -> str:
        result = word
        for variant in sorted(self.variant_to_letter.keys(), key=len, reverse=True):
            base = self.variant_to_letter[variant]
            if variant == base:
                continue
            if len(variant) == 1:
                pattern = re.escape(variant)
                result = re.sub(pattern, base, result, flags=re.IGNORECASE)
            else:
                # Only replace multi-character variant if it matches the whole word
                if result.lower() == variant:
                    result = base
        for old, new in self.common_replacements.items():
            pattern = re.escape(old)
            result = re.sub(pattern, new, result, flags=re.IGNORECASE)
        return result

    def get_normal_word(self, jejemon_word: str) -> Optional[str]:
        return self.jejemon_to_normal.get(jejemon_word.lower())

    def get_all_jejemon_words(self) -> List[str]:
        return list(self.jejemon_to_normal.keys())

    def get_all_normal_words(self) -> List[str]:
        return list(self.jejemon_to_normal.values())

    def add_mapping(self, jejemon: str, normal: str):
        self.jejemon_to_normal[jejemon.lower()] = normal.lower()
        self.lexicon['jejemon_to_normal'] = self.jejemon_to_normal