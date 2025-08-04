
import React, { useEffect, useReducer, useCallback } from 'react';
import { GAME_CONFIG, COLORS } from '../../utils/constants';
import { useGameLoop } from '../../hooks/useGameLoop';
import { useInput } from '../../hooks/useInput';
import { useWordValidator } from '../../hooks/useWordValidator';
import { getRandomPosition, getRandomLetter, createParticles } from '../../utils/helpers';
import ScoreDisplay from '../ScoreDisplay/ScoreDisplay';
import ControlPanel from '../ControlPanel/ControlPanel';
import '../../styles/GameStyles.css';

export interface Position {
  x: number;
  y: number;
}

export interface Food {
  position: Position;
  letter: string;
  spawnTime: number;
}

export type Direction = 'UP' | 'DOWN' | 'LEFT' | 'RIGHT';

export const Directions = {
  UP: 'UP' as Direction,
  DOWN: 'DOWN' as Direction,
  LEFT: 'LEFT' as Direction,
  RIGHT: 'RIGHT' as Direction
};

interface GameState {
  snake: Position[];
  foods: Food[];
  score: number;
  gameTime: number;
  isGameOver: boolean;
  collectedLetters: string[];
  direction: Direction;
  wordsCollected: number;
  isGameStarted: boolean;
  countdownValue: number;
  lastWordFormed: string | null;
}

type WordValidationPayload = string | { word: string; startIndex: number; endIndex: number };

type GameAction = 
  | { type: 'MOVE_SNAKE' }
  | { type: 'SET_DIRECTION'; payload: Direction }
  | { type: 'SPAWN_FOOD' }
  | { type: 'GAME_OVER' }
  | { type: 'UPDATE_TIME'; payload: number }
  | { type: 'CONSUME_FOOD'; payload: Food }
  | { type: 'VALIDATE_WORD'; payload: WordValidationPayload }
  | { type: 'START_GAME' }
  | { type: 'UPDATE_COUNTDOWN'; payload: number }
  | { type: 'RESET_GAME' };

const initialState: GameState = {
  snake: [{ x: 10, y: 10 }],
  foods: [],
  score: 0,
  gameTime: 0,
  isGameOver: false,
  collectedLetters: [],
  direction: Directions.RIGHT,
  wordsCollected: 0,
  isGameStarted: false,
  countdownValue: 3,
  lastWordFormed: null
};

function gameReducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case 'START_GAME':
      return { ...state, isGameStarted: true };
      
    case 'UPDATE_COUNTDOWN':
      return { ...state, countdownValue: action.payload };
      
    case 'SET_DIRECTION':
      // Prevent snake from reversing
      if (
        (action.payload === Directions.UP && state.direction === Directions.DOWN) ||
        (action.payload === Directions.DOWN && state.direction === Directions.UP) ||
        (action.payload === Directions.LEFT && state.direction === Directions.RIGHT) ||
        (action.payload === Directions.RIGHT && state.direction === Directions.LEFT)
      ) {
        return state;
      }
      return { ...state, direction: action.payload };
      
    case 'MOVE_SNAKE': {
      // Don't move if game hasn't started or is over
      if (!state.isGameStarted || state.isGameOver || state.countdownValue > 0) {
        return state;
      }
      
      const newSnake = [...state.snake];
      const head = { ...newSnake[0] };

      switch (state.direction) {
        case Directions.UP:
          head.y -= 1;
          break;
        case Directions.DOWN:
          head.y += 1;
          break;
        case Directions.LEFT:
          head.x -= 1;
          break;
        case Directions.RIGHT:
          head.x += 1;
          break;
      }

      newSnake.unshift(head);

      // Check for food consumption before popping the tail
      const foodIndex = state.foods.findIndex(
        (food) => food.position.x === head.x && food.position.y === head.y
      );

      if (foodIndex === -1) {
        newSnake.pop();
      }

      return { ...state, snake: newSnake };
    }
    
    case 'SPAWN_FOOD':
      // Don't spawn food if game hasn't started or is over
      if (!state.isGameStarted || state.isGameOver || state.countdownValue > 0) {
        return state;
      }
      
      if (state.foods.length < GAME_CONFIG.MAX_FOODS_ON_SCREEN) {
        // Avoid spawning food on snake
        const avoidPositions = [...state.snake, ...state.foods.map(f => f.position)];
        const newPosition = getRandomPosition(GAME_CONFIG.GRID_SIZE, GAME_CONFIG.GRID_SIZE, avoidPositions);
        
        const newFood: Food = {
          position: newPosition,
          letter: getRandomLetter(),
          spawnTime: Date.now(),
        };
        return { ...state, foods: [...state.foods, newFood] };
      }
      return state;
      
    case 'CONSUME_FOOD': {
      const food = action.payload;
      const newFoods = state.foods.filter(f => f !== food);
      const newCollectedLetters = [...state.collectedLetters, food.letter];
      return { ...state, foods: newFoods, collectedLetters: newCollectedLetters };
    }
    
    case 'VALIDATE_WORD': {
      // Handle both string and object payload formats
      let word: string;
      let startIndex = 0;
      let endIndex: number;
      
      if (typeof action.payload === 'string') {
        // Old format: just the word
        word = action.payload;
        endIndex = state.collectedLetters.length - 1;
      } else {
        // New format: object with word and indices
        word = action.payload.word;
        startIndex = action.payload.startIndex;
        endIndex = action.payload.endIndex;
      }
      
      const newScore = state.score + word.length;
      const newWordsCollected = state.wordsCollected + 1;
      
      // Create a new snake without the segments that formed the word
      let newSnake = [...state.snake];
      const segmentsToRemove = endIndex - startIndex + 1;
      
      // Remove segments from the snake
      // For words at the beginning of the snake, we keep the head and remove from the end
      // For words in the middle or end, we remove the specific segments
      if (startIndex === 0) {
        // Word at the beginning - remove from end as before
        newSnake = newSnake.slice(0, newSnake.length - segmentsToRemove);
      } else {
        // Word in the middle or end - remove specific segments
        // We need to keep the segments before startIndex and after endIndex
        // +1 to account for the head which isn't part of collectedLetters
        const actualStartIndex = startIndex + 1;
        const actualEndIndex = endIndex + 1;
        newSnake = [
          ...newSnake.slice(0, actualStartIndex),
          ...newSnake.slice(actualEndIndex + 1)
        ];
      }
      
      // Update collected letters - remove the ones that formed the word
      let newCollectedLetters = [...state.collectedLetters];
      newCollectedLetters.splice(startIndex, segmentsToRemove);
      
      return { 
        ...state, 
        score: newScore, 
        wordsCollected: newWordsCollected,
        collectedLetters: newCollectedLetters, 
        snake: newSnake,
        lastWordFormed: word
      };
    }
    
    case 'GAME_OVER':
      return { ...state, isGameOver: true };
      
    case 'UPDATE_TIME':
      return { ...state, gameTime: state.gameTime + action.payload };
    
    case 'RESET_GAME':
      return {
        ...initialState,
        isGameStarted: true,  // Start the game immediately
        countdownValue: 3     // Start with countdown
      };
      
    default:
      return state;
  }
}

const GameBoard: React.FC = () => {
  const [state, dispatch] = useReducer(gameReducer, initialState);
  const direction = useInput();
  const wordValidator = useWordValidator();

  // Start game and countdown
  useEffect(() => {
    // Start countdown when any key is pressed
    const handleKeyPress = () => {
      if (!state.isGameStarted && !state.isGameOver) {
        dispatch({ type: 'START_GAME' });
        
        // Start countdown
        let count = 3;
        const countdownInterval = setInterval(() => {
          count -= 1;
          dispatch({ type: 'UPDATE_COUNTDOWN', payload: count });
          
          if (count <= 0) {
            clearInterval(countdownInterval);
          }
        }, 1000);
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [state.isGameStarted, state.isGameOver]);

  // Set direction based on input
  useEffect(() => {
    if (direction !== null) {
      dispatch({ type: 'SET_DIRECTION', payload: direction });
    }
  }, [direction]);

  // Create particle effect when a word is formed
  useEffect(() => {
    if (state.lastWordFormed) {
      const head = state.snake[0];
      const x = (head.x + 1) * GAME_CONFIG.CELL_SIZE;
      const y = (head.y + 1) * GAME_CONFIG.CELL_SIZE;
      
      // Create particles at the head position with the valid word color
      createParticles(x, y, COLORS.VALID_WORD, state.lastWordFormed.length * 2);
      
      // Show word formed notification
      const wordElement = document.createElement('div');
      wordElement.className = 'word-formed';
      wordElement.textContent = state.lastWordFormed.toUpperCase();
      wordElement.style.left = `${x}px`;
      wordElement.style.top = `${y - 20}px`;
      
      const gameBoard = document.querySelector('.game-board');
      if (gameBoard) {
        gameBoard.appendChild(wordElement);
        
        // Remove word notification after animation
        setTimeout(() => {
          if (gameBoard.contains(wordElement)) {
            gameBoard.removeChild(wordElement);
          }
        }, 1500);
      }
    }
  }, [state.lastWordFormed]);

  // Game loop
  const gameLoop = useCallback(() => {
    if (state.isGameOver || !state.isGameStarted || state.countdownValue > 0) return;

    dispatch({ type: 'MOVE_SNAKE' });

    // Check for collisions with walls
    const head = state.snake[0];
    if (
      head.x < 0 ||
      head.x >= GAME_CONFIG.GRID_SIZE ||
      head.y < 0 ||
      head.y >= GAME_CONFIG.GRID_SIZE
    ) {
      dispatch({ type: 'GAME_OVER' });
      return;
    }

    // Check for collisions with self
    for (let i = 1; i < state.snake.length; i++) {
      if (state.snake[i].x === head.x && state.snake[i].y === head.y) {
        dispatch({ type: 'GAME_OVER' });
        return;
      }
    }

    // Check for food consumption
    const foodIndex = state.foods.findIndex(
      (food) => food.position.x === head.x && food.position.y === head.y
    );

    if (foodIndex !== -1) {
      const food = state.foods[foodIndex];
      dispatch({ type: 'CONSUME_FOOD', payload: food });
    }

    // Check if snake is too long
    if (state.snake.length > GAME_CONFIG.MAX_SNAKE_LETTERS) {
      dispatch({ type: 'GAME_OVER' });
      return;
    }

    // Check if we have valid words anywhere in the snake
    if (state.collectedLetters.length >= 3) {
      // First check the entire string as before
      const fullWord = state.collectedLetters.join('').toLowerCase();
      if (wordValidator && wordValidator.isValidWord(fullWord)) {
        dispatch({ type: 'VALIDATE_WORD', payload: fullWord });
        return;
      }
      
      // Then check for valid words of at least 3 letters anywhere in the string
      for (let startIdx = 0; startIdx < state.collectedLetters.length - 2; startIdx++) {
        for (let endIdx = startIdx + 2; endIdx < state.collectedLetters.length; endIdx++) {
          const subWord = state.collectedLetters.slice(startIdx, endIdx + 1).join('').toLowerCase();
          if (wordValidator && wordValidator.isValidWord(subWord)) {
            dispatch({ type: 'VALIDATE_WORD', payload: { word: subWord, startIndex: startIdx, endIndex: endIdx } });
            return;
          }
        }
      }
    }
  }, [state, wordValidator]);

  // Run game loop on interval with configured snake speed
  useGameLoop(gameLoop, GAME_CONFIG.SNAKE_SPEED, 0);

  // Spawn food on interval
  useEffect(() => {
    if (state.isGameOver || !state.isGameStarted || state.countdownValue > 0) return;
    
    // Only spawn food if we're below the maximum
    if (state.foods.length >= GAME_CONFIG.MAX_FOODS_ON_SCREEN) return;

    const foodInterval = setInterval(() => {
      // Double-check we're still below the max before dispatching
      if (state.foods.length < GAME_CONFIG.MAX_FOODS_ON_SCREEN) {
        dispatch({ type: 'SPAWN_FOOD' });
      }
    }, GAME_CONFIG.FOOD_SPAWN_INTERVAL);

    return () => clearInterval(foodInterval);
  }, [state.isGameOver, state.isGameStarted, state.countdownValue, state.foods.length]);

  // Update game time
  useEffect(() => {
    if (state.isGameOver || !state.isGameStarted || state.countdownValue > 0) return;

    const timeInterval = setInterval(() => {
      dispatch({ type: 'UPDATE_TIME', payload: 1 });
    }, 1000);

    return () => clearInterval(timeInterval);
  }, [state.isGameOver, state.isGameStarted, state.countdownValue]);

  // Get CSS classes for different game states
  const getGameBoardClass = () => {
    let classes = 'game-board';
    if (state.isGameOver) classes += ' game-over';
    if (!state.isGameStarted) classes += ' not-started';
    return classes;
  };

  return (
    <div className="game-container">
      {!state.isGameStarted && !state.isGameOver && (
        <div className="start-message">Press any key to start</div>
      )}
      
      {state.countdownValue > 0 && state.isGameStarted && (
        <div className="countdown">{state.countdownValue}</div>
      )}
      
      <div
        className={getGameBoardClass()}
        style={{
          gridTemplateColumns: `repeat(${GAME_CONFIG.GRID_SIZE}, ${GAME_CONFIG.CELL_SIZE}px)`,
          gridTemplateRows: `repeat(${GAME_CONFIG.GRID_SIZE}, ${GAME_CONFIG.CELL_SIZE}px)`,
        }}
      >
        {/* Render snake */}
        {state.snake.map((segment, index) => {
          const isHead = index === 0;
          const hasFoodLetter = index < state.collectedLetters.length;
          const segmentClass = `snake-segment ${isHead ? 'snake-head' : ''} ${hasFoodLetter ? 'has-letter' : ''}`;
          
          return (
            <div
              key={`snake-${index}`}
              className={segmentClass}
              style={{
                gridColumn: segment.x + 1,
                gridRow: segment.y + 1,
                backgroundColor: isHead ? COLORS.SNAKE_HEAD : COLORS.PRIMARY_SNAKE,
              }}
            >
              {hasFoodLetter ? state.collectedLetters[index] : ''}
            </div>
          );
        })}

        {/* Render food */}
        {state.foods.map((food, index) => {
          const isVowel = 'AEIOU'.includes(food.letter);
          return (
            <div
              key={`food-${index}`}
              className={`food ${isVowel ? 'vowel' : 'consonant'}`}
              style={{
                gridColumn: food.position.x + 1,
                gridRow: food.position.y + 1,
              }}
            >
              {food.letter}
            </div>
          );
        })}
        
        {/* Particles are now rendered directly via DOM manipulation */}
      </div>

      <ScoreDisplay 
        score={state.score} 
        time={state.gameTime} 
        wordsCollected={state.wordsCollected} 
      />
      
      {state.isGameOver && (
        <div className="game-over-message">
          Game Over! Your snake got too long.
          <div className="final-score">
            Final Score: {state.score} points<br />
            Words Collected: {state.wordsCollected}<br />
            Time Survived: {state.gameTime} seconds
          </div>
        </div>
      )}
      
      <ControlPanel isGameOver={state.isGameOver} onRestart={() => dispatch({ type: 'RESET_GAME' })} />
    </div>
  );
};

export default GameBoard;
