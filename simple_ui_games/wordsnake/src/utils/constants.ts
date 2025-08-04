
export const GAME_CONFIG = {
  GRID_SIZE: 20,              // Grid dimensions (20x20 grid)
  CELL_SIZE: 25,              // Cell size in pixels
  SNAKE_SPEED: 350,           // Movement speed in milliseconds (much slower for better control)
  FOOD_SPAWN_INTERVAL: 3000,  // New letter every 3 seconds
  MAX_FOODS_ON_SCREEN: 20,    // Pause spawning at 20 letters
  MAX_SNAKE_LETTERS: 10,      // Death condition (increased from 8)
  VOWEL_PROBABILITY: 0.4,     // 40% chance for vowels (increased from 33%)
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
