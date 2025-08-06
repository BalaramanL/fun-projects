
export const GAME_CONFIG = {
  GRID_SIZE: 20,              // Grid dimensions (20x20 grid)
  CELL_SIZE: 25,              // Cell size in pixels
  SNAKE_SPEED: 300,           // Movement speed in milliseconds (slightly slower for better control)
  FOOD_SPAWN_INTERVAL: 5000,  // New letter every 5 seconds
  MAX_FOODS_ON_SCREEN: 20,    // Pause spawning at 20 letters
  MAX_SNAKE_LETTERS: 8,       // Death condition (as per original rules)
  VOWEL_PROBABILITY: 0.45,    // 45% chance of generating a vowels (1 in 4 letters)
  INITIAL_DELAY: 3000,        // 3 second delay before game starts
  ANIMATION_SPEED: 300        // Animation duration in milliseconds
};

export const COLORS = {
  PRIMARY_SNAKE: '#2ECC71',
  SNAKE_HEAD: '#27AE60',
  FOOD_LETTER: '#E74C3C',
  VALID_WORD: '#F39C12',
  BACKGROUND: '#1A1A1A',
  GRID_LINES: '#2C3E50',
  UI_TEXT: '#ECF0F1',
  ACCENT: '#9B59B6'
};
