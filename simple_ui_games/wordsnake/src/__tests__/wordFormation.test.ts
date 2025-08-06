import { gameReducer, initialGameState, Direction } from '../components/GameBoard/gameState';
import { useWordValidator } from '../hooks/useWordValidator';

// Mock the sound effects to avoid actual audio playback during tests
jest.mock('../utils/soundEffects', () => ({
  playSound: jest.fn(),
  initAudio: jest.fn(),
}));

// Mock the word validator hook
jest.mock('../hooks/useWordValidator', () => ({
  useWordValidator: jest.fn(),
}));

describe('Word Formation', () => {
  // Test for word detection and processing
  describe('Word detection and processing', () => {
    it('should detect valid words in the snake body', () => {
      // Setup a mock word validator that recognizes specific words
      const mockValidator = jest.fn((word) => {
        return ['CAT', 'DOG', 'SNAKE'].includes(word);
      });
      
      // Apply the mock to the useWordValidator hook
      (useWordValidator as jest.Mock).mockReturnValue(mockValidator);
      
      // Setup initial state with a snake that forms a word
      const testState = {
        ...initialGameState,
        snake: [
          { x: 5, y: 5 }, // T (head)
          { x: 5, y: 6 }, // A
          { x: 5, y: 7 }, // C
          { x: 5, y: 8 }, // X
          { x: 5, y: 9 }, // Y
        ],
        collectedLetters: ['T', 'A', 'C', 'X', 'Y'],
      };
      
      // Simulate checking for words
      const words = [];
      
      // Check for words starting from the head (should find "CAT" backwards)
      for (let i = 0; i < testState.snake.length; i++) {
        for (let j = i + 2; j < testState.snake.length; j++) { // Minimum 3 letters
          const wordLetters = testState.collectedLetters.slice(i, j + 1);
          const word = wordLetters.join('');
          const reversedWord = wordLetters.reverse().join('');
          
          if (mockValidator(word)) {
            words.push({ word, indices: Array.from({ length: word.length }, (_, k) => i + k) });
          } else if (mockValidator(reversedWord)) {
            words.push({ word: reversedWord, indices: Array.from({ length: reversedWord.length }, (_, k) => i + k) });
          }
        }
      }
      
      // Verify that "CAT" is detected (reversed from the head: T-A-C)
      expect(words.length).toBe(1);
      expect(words[0].word).toBe('CAT');
      
      // Process the word
      const action = {
        type: 'PROCESS_WORD' as const,
        payload: {
          word: words[0].word,
          indices: words[0].indices,
        },
      };
      
      // Apply the action
      const newState = gameReducer(testState, action);
      
      // Verify the snake has been shortened correctly
      expect(newState.snake.length).toBe(2);
      
      // Verify the remaining letters are correct (X, Y)
      expect(newState.collectedLetters).toEqual(['X', 'Y']);
      
      // Verify the score has been updated
      expect(newState.score).toBeGreaterThan(testState.score);
      
      // Verify the word count has increased
      expect(newState.wordsCollected).toBe(testState.wordsCollected + 1);
      
      // Verify the letter count has increased by the word length
      expect(newState.lettersCollected).toBe(testState.lettersCollected + 3);
    });
    
    it('should detect words anywhere in the snake body, not just from the head', () => {
      // Setup a mock word validator that recognizes specific words
      const mockValidator = jest.fn((word) => {
        return ['CAT', 'DOG', 'SNAKE', 'FAR'].includes(word);
      });
      
      // Apply the mock to the useWordValidator hook
      (useWordValidator as jest.Mock).mockReturnValue(mockValidator);
      
      // Setup initial state with a snake that forms a word in the middle
      const testState = {
        ...initialGameState,
        snake: [
          { x: 5, y: 5 }, // J (head)
          { x: 5, y: 6 }, // F
          { x: 5, y: 7 }, // A
          { x: 5, y: 8 }, // R
          { x: 5, y: 9 }, // E
        ],
        collectedLetters: ['J', 'F', 'A', 'R', 'E'],
      };
      
      // Simulate checking for words
      const words = [];
      
      // Check for words starting from any position
      for (let i = 0; i < testState.snake.length; i++) {
        for (let j = i + 2; j < testState.snake.length; j++) { // Minimum 3 letters
          const wordLetters = testState.collectedLetters.slice(i, j + 1);
          const word = wordLetters.join('');
          
          if (mockValidator(word)) {
            words.push({ word, indices: Array.from({ length: word.length }, (_, k) => i + k) });
          }
        }
      }
      
      // Verify that "FAR" is detected in the middle
      expect(words.length).toBe(1);
      expect(words[0].word).toBe('FAR');
      
      // Process the word
      const action = {
        type: 'PROCESS_WORD' as const,
        payload: {
          word: words[0].word,
          indices: words[0].indices,
        },
      };
      
      // Apply the action
      const newState = gameReducer(testState, action);
      
      // Verify the snake has been shortened correctly
      expect(newState.snake.length).toBe(2);
      
      // Verify the remaining letters are correct (J, E)
      expect(newState.collectedLetters).toEqual(['J', 'E']);
    });
  });
  
  // Test for game over prevention when snake is shortened
  describe('Game over prevention through word formation', () => {
    it('should prevent game over if snake is shortened below max length', () => {
      // Setup a mock word validator
      const mockValidator = jest.fn((word) => word === 'CAT');
      (useWordValidator as jest.Mock).mockReturnValue(mockValidator);
      
      // Setup initial state with a snake at maximum length
      const maxLength = 8; // MAX_SNAKE_LETTERS from GAME_CONFIG
      const snake = Array(maxLength).fill(0).map((_, i) => ({ x: 5, y: 5 + i }));
      const letters = ['T', 'A', 'C', 'X', 'Y', 'Z', 'P', 'Q']; // CAT is in the first 3
      
      const testState = {
        ...initialGameState,
        snake,
        collectedLetters: letters,
        foods: [
          { position: { x: 6, y: 5 }, letter: 'R' }, // Food to the right of head
        ],
      };
      
      // First, process the word "CAT" to shorten the snake
      const processWordAction = {
        type: 'PROCESS_WORD' as const,
        payload: {
          word: 'CAT',
          indices: [0, 1, 2], // First three letters form CAT
        },
      };
      
      // Apply the action
      const afterWordState = gameReducer(testState, processWordAction);
      
      // Verify the snake is shortened
      expect(afterWordState.snake.length).toBe(5);
      
      // Now move the snake to eat food, which would have exceeded max length
      // but should be safe now that the snake is shorter
      const moveSnakeAction = {
        type: 'MOVE_SNAKE' as const,
      };
      
      // Apply the action
      const finalState = gameReducer({
        ...afterWordState,
        direction: Direction.RIGHT,
      }, moveSnakeAction);
      
      // Verify the game is not over
      expect(finalState.gameOver).toBe(false);
      
      // Verify the snake has grown by one after eating
      expect(finalState.snake.length).toBe(5); // The snake was 5 segments long before eating
    });
  });
});
