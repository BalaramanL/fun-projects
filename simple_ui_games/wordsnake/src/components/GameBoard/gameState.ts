import { GAME_CONFIG } from '../../utils/constants';
import type { Position } from '../../utils/helpers';
import { playSound } from '../../utils/soundEffects';

// Define Direction enum
export enum Direction {
  UP = 'UP',
  DOWN = 'DOWN',
  LEFT = 'LEFT',
  RIGHT = 'RIGHT'
}

// Define Food interface
export interface Food {
  position: Position;
  letter: string;
}

// Define GameState interface
export interface GameState {
  snake: Position[];
  foods: Food[];
  direction: Direction;
  nextDirection: Direction;
  score: number;
  wordsCollected: number;
  lettersCollected: number;
  gameOver: boolean;
  isPaused: boolean;
  isGameStarted: boolean;
  countdownActive: boolean;
  gameTime: number;
  collectedLetters: string[];
}

// Define Action types
export type GameAction =
  | { type: 'MOVE_SNAKE' }
  | { type: 'CHANGE_DIRECTION'; payload: Direction }
  | { type: 'ADD_FOOD'; payload: Food }
  | { type: 'COLLECT_FOOD'; payload: Food }
  | { type: 'PROCESS_WORD'; payload: { word: string; indices: number[] } }
  | { type: 'TOGGLE_PAUSE' }
  | { type: 'START_GAME' }
  | { type: 'END_GAME' }
  | { type: 'UPDATE_TIME' }
  | { type: 'RESET_GAME' }
  | { type: 'SET_COUNTDOWN'; payload: boolean };

// Initial game state
export const initialGameState: GameState = {
  snake: [{ x: Math.floor(GAME_CONFIG.GRID_SIZE / 2), y: Math.floor(GAME_CONFIG.GRID_SIZE / 2) }],
  foods: [],
  direction: Direction.RIGHT,
  nextDirection: Direction.RIGHT,
  score: 0,
  wordsCollected: 0,
  lettersCollected: 0,
  gameOver: false,
  isPaused: true, // Start paused to show rules
  isGameStarted: false,
  countdownActive: false,
  gameTime: 0,
  collectedLetters: [],
};

// Game reducer function
export const gameReducer = (state: GameState, action: GameAction): GameState => {
  switch (action.type) {
    case 'MOVE_SNAKE': {
      if (state.isPaused || state.countdownActive || state.gameOver) {
        return state;
      }

      // Update direction from nextDirection
      const direction = state.nextDirection;

      // Calculate new head position
      const head = state.snake[0];
      let newHead: Position;

      // Check for opposite directions to prevent immediate death
      const isOppositeDirection = 
        (direction === Direction.UP && state.direction === Direction.DOWN) ||
        (direction === Direction.DOWN && state.direction === Direction.UP) ||
        (direction === Direction.LEFT && state.direction === Direction.RIGHT) ||
        (direction === Direction.RIGHT && state.direction === Direction.LEFT);

      // If trying to move in the opposite direction of current travel, keep current direction
      const effectiveDirection = isOppositeDirection ? state.direction : direction;

      // Calculate new head position based on direction
      switch (effectiveDirection) {
        case Direction.UP:
          newHead = { x: head.x, y: head.y - 1 };
          break;
        case Direction.DOWN:
          newHead = { x: head.x, y: head.y + 1 };
          break;
        case Direction.LEFT:
          newHead = { x: head.x - 1, y: head.y };
          break;
        case Direction.RIGHT:
          newHead = { x: head.x + 1, y: head.y };
          break;
        default:
          newHead = { ...head };
      }

      // Check for wall collision
      if (
        newHead.x < 0 ||
        newHead.x >= GAME_CONFIG.GRID_SIZE ||
        newHead.y < 0 ||
        newHead.y >= GAME_CONFIG.GRID_SIZE
      ) {
        // Play death sound
        playSound('gameOver');
        return {
          ...state,
          gameOver: true,
        };
      }

      // Check for self collision (skip head)
      for (let i = 1; i < state.snake.length; i++) {
        if (state.snake[i].x === newHead.x && state.snake[i].y === newHead.y) {
          // Play death sound
          playSound('gameOver');
          return {
            ...state,
            gameOver: true,
          };
        }
      }

      // Check for food collision
      const foodIndex = state.foods.findIndex(
        (food) => food.position.x === newHead.x && food.position.y === newHead.y
      );

      if (foodIndex !== -1) {
        // Collect the food
        const food = state.foods[foodIndex];
        const newFoods = [...state.foods];
        newFoods.splice(foodIndex, 1);

        // Play eat sound
        playSound('eat');

        // Add letter to collected letters
        const newCollectedLetters = [...state.collectedLetters, food.letter];

        // Create new snake with food
        const newSnake = [newHead, ...state.snake];

        return {
          ...state,
          snake: newSnake,
          foods: newFoods,
          direction: effectiveDirection,
          collectedLetters: newCollectedLetters,
        };
      }

      // Move snake (remove tail)
      const newSnake = [newHead, ...state.snake.slice(0, -1)];

      return {
        ...state,
        snake: newSnake,
        direction: effectiveDirection,
      };
    }

    case 'CHANGE_DIRECTION': {
      if (state.isPaused || state.countdownActive || state.gameOver) {
        return state;
      }

      // Play turn sound
      if (action.payload !== state.direction) {
        playSound('turn');
      }

      return {
        ...state,
        nextDirection: action.payload,
      };
    }

    case 'ADD_FOOD': {
      return {
        ...state,
        foods: [...state.foods, action.payload],
      };
    }

    case 'COLLECT_FOOD': {
      const foodIndex = state.foods.findIndex(
        (food) => 
          food.position.x === action.payload.position.x && 
          food.position.y === action.payload.position.y
      );

      if (foodIndex === -1) {
        return state;
      }

      const newFoods = [...state.foods];
      newFoods.splice(foodIndex, 1);

      return {
        ...state,
        foods: newFoods,
      };
    }

    case 'PROCESS_WORD': {
      // Extract word and indices from payload
      const { word, indices } = action.payload;
      
      // Calculate score based on word length (longer words = more points)
      const wordScore = Math.pow(2, word.length - 2) * 10;
      
      // Play word formed sound
      playSound('wordFormed');
      
      // Create new snake by removing only the word segments
      let newSnake = [...state.snake];
      
      // Sort indices in descending order to remove from end to beginning
      // This prevents index shifting issues when removing multiple items
      const sortedIndices = [...indices].sort((a, b) => b - a);
      
      // Create a new collectedLetters array by removing the same indices
      let newCollectedLetters = [...state.collectedLetters];
      
      // Remove the segments that form the word
      sortedIndices.forEach(index => {
        newSnake.splice(index, 1);
        newCollectedLetters.splice(index, 1);
      });
      
      // If snake is empty, add a new head
      if (newSnake.length === 0) {
        newSnake.push({ x: Math.floor(GAME_CONFIG.GRID_SIZE / 2), y: Math.floor(GAME_CONFIG.GRID_SIZE / 2) });
      }
      
      return {
        ...state,
        snake: newSnake,
        score: state.score + wordScore,
        wordsCollected: state.wordsCollected + 1,
        lettersCollected: state.lettersCollected + word.length,
        collectedLetters: newCollectedLetters,
      };
    }

    case 'TOGGLE_PAUSE': {
      if (state.gameOver) {
        return state;
      }

      return {
        ...state,
        isPaused: !state.isPaused,
      };
    }

    case 'START_GAME': {
      return {
        ...state,
        isGameStarted: true,
        isPaused: false,
        countdownActive: false,
      };
    }

    case 'END_GAME': {
      return {
        ...state,
        gameOver: true,
      };
    }

    case 'UPDATE_TIME': {
      if (state.isPaused || !state.isGameStarted || state.gameOver) {
        return state;
      }

      return {
        ...state,
        gameTime: state.gameTime + 1,
      };
    }

    case 'RESET_GAME': {
      return {
        ...initialGameState
      };
    }

    case 'SET_COUNTDOWN': {
      return {
        ...state,
        countdownActive: action.payload
      };
    }

    default:
      return state;
  }
};
