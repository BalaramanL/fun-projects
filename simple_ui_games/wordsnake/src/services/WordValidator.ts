interface TrieNode {
  [key: string]: TrieNode | boolean;
}

export class WordValidator {
  private trie: TrieNode = {};
  private loaded: boolean = false;

  async loadDictionary() {
    try {
      const response = await fetch('/database.json');
      const data = await response.json();
      this.trie = data.trie;
      this.loaded = true;
      console.log('Dictionary loaded successfully');
    } catch (error) {
      console.error("Failed to load dictionary:", error);
    }
  }

  isValidWord(word: string): boolean {
    // Don't validate if dictionary isn't loaded or word is too short
    if (!this.loaded) {
      console.warn('Dictionary not loaded yet, cannot validate word:', word);
      return false;
    }
    
    if (word.length < 3) {
      console.log('Word too short (less than 3 letters):', word);
      return false;
    }
    
    let node = this.trie;
    for (const char of word.toUpperCase()) {
      if (!node[char]) {
        console.log(`Word "${word}" is invalid: character "${char}" not found in trie`);
        return false;
      }
      node = node[char] as TrieNode;
    }
    
    const isValid = node['$'] === true;
    console.log(`Word "${word}" is ${isValid ? 'valid' : 'invalid'}`);
    return isValid;
  }
}