interface TrieNode {
  [key: string]: TrieNode | boolean;
}

export class WordValidator {
  private trie: TrieNode = {};

  async loadDictionary() {
    try {
      const response = await fetch('/database.json');
      const data = await response.json();
      this.trie = data.trie;
    } catch (error) {
      console.error("Failed to load dictionary:", error);
    }
  }

  isValidWord(word: string): boolean {
    let node = this.trie;
    for (const char of word.toUpperCase()) {
      if (!node[char]) {
        return false;
      }
      node = node[char] as TrieNode;
    }
    return node['$'] === true;
  }
}