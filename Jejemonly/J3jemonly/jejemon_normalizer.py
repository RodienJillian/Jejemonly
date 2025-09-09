from typing import List, Dict, Tuple
from .text_preprocessor import TextPreprocessor
from .tokenizer import Tokenizer
from .edit_distance import EditDistance
from .fuzzy_matcher import FuzzyMatcher
from .lemmatizer import Lemmatizer
from .lexicon_manager import LexiconManager

class JejemonNormalizer:
    def __init__(self, lexicon_file: str = './lexicon/dictionary.json', characters_file: str = './lexicon/characters.json', context_rules_file: str = './lexicon/context_rules.json'):
        self.preprocessor = TextPreprocessor()
        self.tokenizer = Tokenizer()
        self.fuzzy_matcher = FuzzyMatcher(threshold=0.6)
        self.lemmatizer = Lemmatizer()
        self.lexicon_manager = LexiconManager(lexicon_file, characters_file)
        self.context_replacements = self._load_context_rules(context_rules_file)
        self.meaningful_punctuation = {
            "'", '"', '-', '_', '.', '!', '?', ',', ';', ':', '+',
            '(', ')', '[', ']', '{', '}', '/', '\\', '|', '@', '#', '$', '%'
        }

    def _load_context_rules(self, context_rules_file: str) -> dict:
        import json
        try:
            with open(context_rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"[DEBUG] Context rules loaded from {context_rules_file}")
                return data.get('context_aware_rules', {})
        except FileNotFoundError:
            print(f"Warning: Context rules file '{context_rules_file}' not found. Using empty rules.")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in context rules file '{context_rules_file}': {e}")
            return {}

    def _should_apply_character_replacement(self, word: str) -> bool:
        """
        Skip replacement if:
        - Words that are already normal words
        - Words that are already known jejemon words
        - Pure numbers (but allow mixed alphanumeric that could be jejemon)
        - Specific number patterns (dates, times, etc.)
        """
        import re
        
        # Skip if it's already a normal word
        if self.lexicon_manager.is_in_words_txt(word):
            print(f"[DEBUG] Skipping character replacement for '{word}' - already a normal word")
            return False
            
        # Skip if it's already a known jejemon word
        if self.lexicon_manager.get_normal_word(word):
            print(f"[DEBUG] Skipping character replacement for '{word}' - already a known jejemon word")
            return False
        
        # Skip pure numbers (3+ digits to avoid jejemon like "2", "e2", etc.)
        if word.isdigit() and len(word) >= 3:
            print(f"[DEBUG] Skipping character replacement for '{word}' - pure number")
            return False
            
        # Skip specific number patterns (years, dates, times, etc.)
        number_patterns = [
            r'^\d{4}$',  # Years (1999, 2021, etc.)
            r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$',  # Dates (12/31/2021, 1-1-21, etc.)
            r'^\d{1,2}:\d{2}(:\d{2})?([ap]m)?$',  # Times (12:30, 3:45pm, etc.)
            r'^\d+\.\d+$',  # Decimals (3.14, 12.5, etc.)
            r'^\d+,\d+$',  # Numbers with commas (1,000, etc.)
            r'^\d+%$',  # Percentages (50%, etc.)
            r'^#\d+$',  # Hash numbers (#1, #123, etc.)
            r'^\$\d+(\.\d{2})?$',  # Money ($10, $15.50, etc.)
        ]
        
        for pattern in number_patterns:
            if re.match(pattern, word, re.IGNORECASE):
                print(f"[DEBUG] Skipping character replacement for '{word}' - matches number pattern {pattern}")
                return False
        
        # Skip obvious codes/IDs but allow potential jejemon
        # Only skip if it looks like a formal code (uppercase + numbers, or very long)
        alphanumeric_patterns = [
            r'^[A-Z]{2,}\d{2,}$',  # License plates, model numbers (ABC123, ABCD1234, etc.)
            r'^\d{3,}[A-Z]{2,}$',  # Reverse pattern (123ABC, etc.)
            r'^[A-Z0-9]{5,}-[A-Z0-9]{3,}$',  # Long codes with dashes
            r'^[A-Z]{3,}\d{3,}[A-Z]{2,}$',  # Complex mixed patterns
        ]
        
        for pattern in alphanumeric_patterns:
            if re.match(pattern, word, re.IGNORECASE):
                print(f"[DEBUG] Skipping character replacement for '{word}' - matches alphanumeric pattern {pattern}")
                return False
        
        # Allow character replacement for potential jejemon words
        # This includes short mixed alphanumeric like "22o", "e2", "b4", etc.
        print(f"[DEBUG] Allowing character replacement for '{word}' - potential jejemon word")
        return True

    def _apply_context_aware_replacements(self, word: str) -> str:
        import re
        
        print(f"[DEBUG] Applying context-aware replacements to '{word}'")
        
        # Check if we should apply character replacement
        if not self._should_apply_character_replacement(word):
            print(f"[DEBUG] No character replacement needed for '{word}'")
            return word
            
        result = word
        for char, rules in self.context_replacements.items():
            if char in result:
                applied_context_rule = False
                for rule in rules['context_rules']:
                    if re.search(rule['pattern'], result, re.IGNORECASE):
                        old_result = result
                        result = result.replace(char, rule['replacement'])
                        print(f"[DEBUG] Context rule applied: '{old_result}' -> '{result}' (char '{char}' -> '{rule['replacement']}')")
                        applied_context_rule = True
                        break
                if not applied_context_rule:
                    old_result = result
                    result = result.replace(char, rules['default'])
                    print(f"[DEBUG] Default replacement applied: '{old_result}' -> '{result}' (char '{char}' -> '{rules['default']}')")
        
        # Apply variant-to-letter and common replacements
        old_result = result
        result = self.lexicon_manager.apply_character_replacements(result)
        if old_result != result:
            print(f"[DEBUG] Character replacements applied: '{old_result}' -> '{result}'")
        
        return result

    def _evaluate_punctuation_value(self, word: str) -> Tuple[str, bool]:
        print(f"[DEBUG] Evaluating punctuation for '{word}'")
        
        if not any(p in word for p in self.meaningful_punctuation):
            print(f"[DEBUG] No meaningful punctuation in '{word}'")
            return word, False
            
        meaningful_patterns = [
            ("'s", "s"), ("'t", "t"), ("'re", "re"), ("'ve", "ve"), ("'ll", "ll"),
            ("'d", "d"), ("'m", "m"), ("'re", "re"), ("'", ""), ("`", ""), ("'", ""),
        ]
        original_word = word
        modified_word = word
        
        for punct, replacement in meaningful_patterns:
            if punct in modified_word:
                old_modified = modified_word
                modified_word = modified_word.replace(punct, replacement)
                print(f"[DEBUG] Punctuation pattern applied: '{old_modified}' -> '{modified_word}' ('{punct}' -> '{replacement}')")
        
        # Try to map using jejemon_to_normal
        original_mapped = self.lexicon_manager.get_normal_word(original_word)
        modified_mapped = self.lexicon_manager.get_normal_word(modified_word)
        
        if original_mapped:
            print(f"[DEBUG] Original word '{original_word}' maps to '{original_mapped}'")
        if modified_mapped:
            print(f"[DEBUG] Modified word '{modified_word}' maps to '{modified_mapped}'")
        
        if original_mapped and not modified_mapped:
            print(f"[DEBUG] Using original mapping: '{original_word}' -> '{original_mapped}'")
            return original_mapped, False
        if modified_mapped and not original_mapped:
            print(f"[DEBUG] Using modified mapping: '{modified_word}' -> '{modified_mapped}'")
            return modified_mapped, True
        if original_mapped and modified_mapped:
            print(f"[DEBUG] Both mapped, using modified: '{modified_word}' -> '{modified_mapped}'")
            return modified_mapped, True
        
        print(f"[DEBUG] No mapping found, returning original: '{original_word}'")
        return original_word, False

    
    def normalize_word(self, word: str) -> str:
        print(f"[DEBUG] ===== NORMALIZING WORD: '{word}' =====")
        
        if self.lexicon_manager.is_in_words_txt(word):
            print(f"[DEBUG] '{word}' is already in words.txt, returning as-is")
            return word
            
        # First, check direct mapping
        normal_word = self.lexicon_manager.get_normal_word(word)
        if normal_word:
            print(f"[DEBUG] Direct mapping found: '{word}' -> '{normal_word}'")
            return normal_word
        
        # Apply character replacements only if appropriate
        if self._should_apply_character_replacement(word):
            modified_word = self.lexicon_manager.apply_character_replacements(word)
            if modified_word != word:
                print(f"[DEBUG] Character replacements applied: '{word}' -> '{modified_word}'")
                normal_word = self.lexicon_manager.get_normal_word(modified_word)
                if normal_word:
                    print(f"[DEBUG] Modified word maps to: '{modified_word}' -> '{normal_word}'")
                    return normal_word
        
        # Try fuzzy matching
        jejemon_words = self.lexicon_manager.get_all_jejemon_words()
        if jejemon_words:
            print(f"[DEBUG] Attempting fuzzy matching for '{word}'")
            best_match, score = self.fuzzy_matcher.find_best_match(word, jejemon_words)
            print(f"[DEBUG] Best fuzzy match: '{best_match}' with score {score}")
            
            if score > 0.6:
                matched_normal = self.lexicon_manager.get_normal_word(best_match)
                if matched_normal:
                    print(f"[DEBUG] Fuzzy match success: '{word}' -> '{best_match}' -> '{matched_normal}'")
                    return matched_normal
        
        # Try lemmatization then fuzzy matching
        lemmatized = self.lemmatizer.lemmatize(word)
        if lemmatized != word:
            print(f"[DEBUG] Lemmatized: '{word}' -> '{lemmatized}'")
            normal_word = self.lexicon_manager.get_normal_word(lemmatized)
            if normal_word:
                print(f"[DEBUG] Lemmatized word maps to: '{lemmatized}' -> '{normal_word}'")
                return normal_word
            
            if jejemon_words:
                print(f"[DEBUG] Attempting fuzzy matching for lemmatized word '{lemmatized}'")
                best_match, score = self.fuzzy_matcher.find_best_match(lemmatized, jejemon_words)
                print(f"[DEBUG] Best fuzzy match for lemmatized: '{best_match}' with score {score}")
                if score > 0.6:
                    matched_normal = self.lexicon_manager.get_normal_word(best_match)
                    if matched_normal:
                        print(f"[DEBUG] Lemmatized fuzzy match success: '{lemmatized}' -> '{best_match}' -> '{matched_normal}'")
                        return matched_normal
        
        # If no match found, return original word
        print(f"[DEBUG] No normalization found for '{word}', returning original")
        return word

    def normalize_text(self, text: str) -> Dict[str, str]:
        print(f"[DEBUG] ===== NORMALIZING TEXT: '{text}' =====")
        
        result = {
            'original': text,
            'punctuation_evaluated': '',
            'character_replaced': '',
            'tokenized': '',
            'normalized': ''
        }
        
        # Step 1: Apply punctuation evaluation to the entire text
        print(f"[DEBUG] Step 1: Punctuation evaluation")
        punctuation_evaluated_text = self._apply_punctuation_evaluation_to_text(text)
        result['punctuation_evaluated'] = punctuation_evaluated_text
        print(f"[DEBUG] After punctuation evaluation: '{punctuation_evaluated_text}'")
        
        # Step 2: Apply character replacements to the entire text
        print(f"[DEBUG] Step 2: Character replacements")
        character_replaced_text = self._apply_character_replacements_to_text(punctuation_evaluated_text)
        result['character_replaced'] = character_replaced_text
        print(f"[DEBUG] After character replacements: '{character_replaced_text}'")
        
        # Step 3: Tokenize the character-replaced text
        print(f"[DEBUG] Step 3: Tokenization")
        tokens = self.tokenizer.tokenize(character_replaced_text)
        result['tokenized'] = ' '.join(tokens)
        print(f"[DEBUG] Tokens: {tokens}")
        
        # Step 4: Apply word-level normalization to each token
        print(f"[DEBUG] Step 4: Word-level normalization")
        normalized_tokens = []
        for i, token in enumerate(tokens):
            print(f"[DEBUG] Processing token {i+1}/{len(tokens)}: '{token}'")
            normalized_token = self.normalize_word(token)
            normalized_tokens.append(normalized_token)
            print(f"[DEBUG] Token normalized: '{token}' -> '{normalized_token}'")
        
        # Step 5: Detokenize the normalized tokens
        print(f"[DEBUG] Step 5: Detokenization")
        result['normalized'] = self.tokenizer.detokenize(normalized_tokens)
        print(f"[DEBUG] Final result: '{result['normalized']}'")
        
        return result

    def _apply_punctuation_evaluation_to_text(self, text: str) -> str:
        """Apply punctuation evaluation patterns to entire text before tokenization"""
        import re

        print(f"[DEBUG] Applying punctuation evaluation to text: '{text}'")
        
        meaningful_patterns = [
            ("'s", "s"), ("'t", "t"), ("'re", "re"), ("'ve", "ve"),
            ("'ll", "ll"), ("'d", "d"), ("'m", "m"), ("'", ""), ("`", "")
        ]
        
        original_text = text
        for punct, replacement in meaningful_patterns:
            if punct in text:
                old_text = text
                text = text.replace(punct, replacement)
                print(f"[DEBUG] Text punctuation replacement: '{punct}' -> '{replacement}' in '{old_text}' -> '{text}'")

        cleaned_words = []
        for word in text.split():
            original = word
            print(f"[DEBUG] Processing word for punctuation cleanup: '{word}'")

            if self.lexicon_manager.get_normal_word(word):
                print(f"[DEBUG] Word '{word}' has jejemon mapping, keeping as-is")
                cleaned_words.append(word)
                continue

            allowed_inside = {'+', '@'}
            allowed_str = ''.join(allowed_inside)

            cleaned = re.sub(rf"^[{re.escape(''.join(self.meaningful_punctuation - allowed_inside))}]+", "", word)
            cleaned = re.sub(rf"[{re.escape(''.join(self.meaningful_punctuation - allowed_inside))}]+$", "", cleaned)
            
            if cleaned != original:
                print(f"[DEBUG] Punctuation cleaned: '{original}' -> '{cleaned}'")

            cleaned_words.append(cleaned)

        result = ' '.join(cleaned_words)
        if result != original_text:
            print(f"[DEBUG] Final punctuation evaluation result: '{original_text}' -> '{result}'")
        return result

    def _apply_character_replacements_to_text(self, text: str) -> str:
        """Apply context-aware character replacements to entire text"""
        import re
        
        print(f"[DEBUG] Applying character replacements to text: '{text}'")
        
        # Process word by word 
        words = text.split()
        processed_words = []
        
        for i, word in enumerate(words):
            print(f"[DEBUG] Processing word {i+1}/{len(words)} for character replacement: '{word}'")
            
            # Check if we should apply character replacement to this word
            if not self._should_apply_character_replacement(word):
                processed_words.append(word)
                continue
                
            result = word
            
            # Apply context-aware replacements to each word individually
            for char, rules in self.context_replacements.items():
                if char in result:
                    applied_context_rule = False
                    for rule in rules['context_rules']:
                        # Pattern now applies to individual word, not full text
                        if re.search(rule['pattern'], result, re.IGNORECASE):
                            old_result = result
                            result = result.replace(char, rule['replacement'])
                            print(f"[DEBUG] Context rule applied to '{word}': '{old_result}' -> '{result}' ('{char}' -> '{rule['replacement']}')")
                            applied_context_rule = True
                            break
                    if not applied_context_rule:
                        old_result = result
                        result = result.replace(char, rules['default'])
                        print(f"[DEBUG] Default replacement applied to '{word}': '{old_result}' -> '{result}' ('{char}' -> '{rules['default']}')")
            
            # Apply variant-to-letter and common replacements
            old_result = result
            result = self.lexicon_manager.apply_character_replacements(result)
            if old_result != result:
                print(f"[DEBUG] Lexicon character replacements applied to '{word}': '{old_result}' -> '{result}'")
            
            processed_words.append(result)
        
        final_result = ' '.join(processed_words)
        if final_result != text:
            print(f"[DEBUG] Final character replacement result: '{text}' -> '{final_result}'")
        return final_result

    def add_variant(self, letter: str, variant: str):
        print(f"[DEBUG] Adding variant: '{letter}' -> '{variant}'")
        self.lexicon_manager.add_variant(letter, variant)
        self.lexicon_manager.save_characters()

    # def add_word_mapping(self, jejemon: str, normal: str):
    #     self.lexicon_manager.add_mapping(jejemon, normal)
    #     self.lexicon_manager.save_lexicon()

    def get_normalization_confidence(self, original: str, normalized: str) -> float:
        print(f"[DEBUG] Calculating confidence for: '{original}' -> '{normalized}'")
        
        if original == normalized:
            print(f"[DEBUG] No changes made, confidence: 0.0")
            return 0.0
            
        original_tokens = self.tokenizer.tokenize(original)
        normalized_tokens = self.tokenizer.tokenize(normalized)
        print(f"[DEBUG] Original tokens: {original_tokens}")
        print(f"[DEBUG] Normalized tokens: {normalized_tokens}")
        
        if len(original_tokens) != len(normalized_tokens):
            print(f"[DEBUG] Token count mismatch, confidence: 0.5")
            return 0.5
            
        if not original_tokens:
            print(f"[DEBUG] No tokens, confidence: 0.0")
            return 0.0
            
        total_confidence = 0.0
        for i, (orig_word, norm_word) in enumerate(zip(original_tokens, normalized_tokens)):
            if orig_word == norm_word:
                print(f"[DEBUG] Token {i+1} unchanged: '{orig_word}' -> confidence: 1.0")
                total_confidence += 1.0
            else:
                similarity = EditDistance.similarity(orig_word, norm_word)
                print(f"[DEBUG] Token {i+1} changed: '{orig_word}' -> '{norm_word}' -> confidence: {similarity}")
                total_confidence += similarity
        
        final_confidence = total_confidence / len(original_tokens)
        print(f"[DEBUG] Final confidence: {final_confidence}")
        return final_confidence