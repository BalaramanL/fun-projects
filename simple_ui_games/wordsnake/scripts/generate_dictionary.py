import requests
import json
import re
from typing import Set, List
from datetime import datetime

class DictionaryGenerator:
    def __init__(self):
        self.min_word_length = 2
        self.max_word_length = 8
        self.valid_words: Set[str] = set()
    
    def fetch_word_list(self) -> List[str]:
        """Fetch words from multiple sources for comprehensive coverage"""
        sources = [
            "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt",
        ]
        
        all_words = set()
        for source in sources:
            try:
                response = requests.get(source, timeout=30)
                words = response.text.strip().split('\n')
                all_words.update(word.strip().upper() for word in words)
                print(f"Loaded {len(words)} words from {source}")
            except Exception as e:
                print(f"Failed to load from {source}: {e}")
        
        return list(all_words)
    
    def filter_words(self, words: List[str]) -> List[str]:
        """Filter words based on game requirements"""
        filtered = []
        for word in words:
            if (self.min_word_length <= len(word) <= self.max_word_length and
                word.isalpha() and
                not re.search(r'[^A-Z]', word)):
                filtered.append(word)
        
        return sorted(filtered)
    
    def generate_trie_structure(self, words: List[str]) -> dict:
        """Convert word list to trie structure for efficient lookup"""
        trie = {}
        for word in words:
            current = trie
            for char in word:
                if char not in current:
                    current[char] = {}
                current = current[char]
            current['$'] = True  # End of word marker
        return trie
    
    def save_dictionary(self, words: List[str], output_path: str):
        """Save both word list and trie structure"""
        dictionary_data = {
            "version": "1.0",
            "word_count": len(words),
            "words": words,
            "trie": self.generate_trie_structure(words),
            "metadata": {
                "min_length": self.min_word_length,
                "max_length": self.max_word_length,
                "generated_at": str(datetime.now())
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(dictionary_data, f, separators=(',', ':'))
        
        print(f"Dictionary saved to {output_path}")
        print(f"Total words: {len(words)}")

if __name__ == "__main__":
    generator = DictionaryGenerator()
    words = generator.fetch_word_list()
    filtered_words = generator.filter_words(words)
    generator.save_dictionary(filtered_words, "public/database.json")
