import React, { useState, useEffect, useReducer, useRef, useCallback } from 'react';
import { GAME_CONFIG } from '../../utils/constants';
import { getRandomPosition, getRandomLetter, createParticles } from '../../utils/helpers';
import { useWordValidator } from '../../hooks/useWordValidator';
import { initAudio, playSound } from '../../utils/soundEffects';
import { Direction, type GameState, type Food, initialGameState, gameReducer } from './gameState';
import { useGameLoop } from '../../hooks/useGameLoop';
import '../../styles/GameStyles.css';

const GameBoard: React.FC = () => {
  // Game state management
  const [state, dispatch] = useReducer(gameReducer, initialGameState);
  const [countdownValue, setCountdownValue] = useState(3);
  const [showRules, setShowRules] = useState(true);
  
  // Refs
  const gameAreaRef = useRef<HTMLDivElement>(null);
  const wordValidator = useWordValidator();
  
  // Initialize audio system
  useEffect(() => {
    initAudio();
  }, []);

  // Handle keyboard input for snake movement
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (state.gameOver) return;

      // Handle pause with Escape key
      if (e.key === 'Escape') {
        dispatch({ type: 'TOGGLE_PAUSE' });
        return;
      }

      // Don't process direction keys if paused or countdown active
      if (state.isPaused || state.countdownActive) return;

      switch (e.key) {
        case 'ArrowUp':
          dispatch({ type: 'CHANGE_DIRECTION', payload: Direction.UP });
          break;
        case 'ArrowDown':
          dispatch({ type: 'CHANGE_DIRECTION', payload: Direction.DOWN });
          break;
        case 'ArrowLeft':
          dispatch({ type: 'CHANGE_DIRECTION', payload: Direction.LEFT });
          break;
        case 'ArrowRight':
          dispatch({ type: 'CHANGE_DIRECTION', payload: Direction.RIGHT });
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [state.isPaused, state.countdownActive, state.gameOver]);

  // Generate food at regular intervals
  // Food spawn timer
  useEffect(() => {
    if (state.isPaused || state.countdownActive || state.gameOver || !state.isGameStarted) return;
    
    const foodInterval = setInterval(() => {
      if (!state.isPaused && !state.countdownActive && !state.gameOver) {
        console.log(`Food spawn interval triggered, current foods: ${state.foods.length}`);
      
      // Only spawn food if we haven't reached the maximum
      if (state.foods.length >= GAME_CONFIG.MAX_FOODS_ON_SCREEN) {
        console.log(`Maximum food limit reached (${GAME_CONFIG.MAX_FOODS_ON_SCREEN}). Skipping food spawn.`);
        return; // Skip spawning if we've reached the limit
      }
      
      console.log('Spawning new food');
        
        // Get all occupied positions to prevent spawning on snake
        const occupiedPositions = [
          ...state.snake.map(segment => ({ x: segment.x, y: segment.y })),
          ...state.foods.map(food => food.position)
        ];
        
        // Add buffer positions around snake to prevent immediate collisions
        const bufferPositions: {x: number, y: number}[] = [];
        state.snake.forEach(segment => {
          // Add positions adjacent to snake segments
          bufferPositions.push(
            { x: segment.x + 1, y: segment.y },
            { x: segment.x - 1, y: segment.y },
            { x: segment.x, y: segment.y + 1 },
            { x: segment.x, y: segment.y - 1 }
          );
        });
        
        const allOccupied = [...occupiedPositions, ...bufferPositions];
        
        const newPosition = getRandomPosition(
          GAME_CONFIG.GRID_SIZE,
          GAME_CONFIG.GRID_SIZE,
          allOccupied
        );
        
        // Check current vowel ratio to enforce better vowel distribution
        const currentFoods = state.foods.map(food => food.letter);
        const allLetters = [...currentFoods, ...state.collectedLetters];
        const vowelCount = allLetters.filter(letter => /[aeiou]/i.test(letter)).length;
        const totalCount = allLetters.length;
        
        // Improved vowel distribution logic:
        // 1. Always ensure at least 25% vowels (1 in 4)
        // 2. If snake has 3+ letters, ensure at least 30% vowels
        // 3. If no vowels in current foods, force a vowel
        const minVowelRatio = state.snake.length >= 3 ? 0.3 : 0.25;
        const currentVowelRatio = vowelCount / (totalCount || 1);
        const noVowelsInFoods = !currentFoods.some(letter => /[aeiou]/i.test(letter));
        
        // Force a vowel under these conditions
        const forceVowel = 
          (totalCount >= 3 && currentVowelRatio < minVowelRatio) || 
          (currentFoods.length > 0 && noVowelsInFoods);
        
        // Get random letter with vowel enforcement if needed
        const letter = forceVowel ? 
          ['A', 'E', 'I', 'O', 'U'][Math.floor(Math.random() * 5)] : 
          getRandomLetter();
        
        console.log(`Adding food: ${letter} (${forceVowel ? 'forced vowel' : 'random'}) - Current ratio: ${vowelCount}/${totalCount}`);
        
        dispatch({
          type: 'ADD_FOOD',
          payload: { position: newPosition, letter }
        });
      }
    }, GAME_CONFIG.FOOD_SPAWN_INTERVAL);

    return () => clearInterval(foodInterval);
  }, [state.isPaused, state.countdownActive, state.gameOver, state.isGameStarted]);

  // Debug log for food count
  useEffect(() => {
    console.log(`Current food count: ${state.foods.length}/${GAME_CONFIG.MAX_FOODS_ON_SCREEN}`);
  }, [state.foods.length]);
  
  // Update game time
  useEffect(() => {
    if (state.isPaused || !state.isGameStarted || state.gameOver || state.countdownActive) return;

    const timeInterval = setInterval(() => {
      dispatch({ type: 'UPDATE_TIME' });
    }, 1000);

    return () => clearInterval(timeInterval);
  }, [state.isPaused, state.isGameStarted, state.gameOver, state.countdownActive]);

  // Countdown timer
  useEffect(() => {
    if (!state.countdownActive) return;

    let countdownTimer: NodeJS.Timeout;
    
    if (countdownValue > 0) {
      countdownTimer = setTimeout(() => {
        setCountdownValue(prev => prev - 1);
      }, 1000);
    } else {
      // Immediately start the game when countdown reaches 0
      dispatch({ type: 'START_GAME' });
      dispatch({ type: 'SET_COUNTDOWN', payload: false }); // Turn off countdown
      setCountdownValue(3); // Reset for next time
    }

    return () => {
      if (countdownTimer) clearTimeout(countdownTimer);
    };
  }, [countdownValue, state.countdownActive]);

  // Check for game over condition (snake too long)
  useEffect(() => {
    if (state.snake.length > GAME_CONFIG.MAX_SNAKE_LETTERS && !state.gameOver) {
      dispatch({ type: 'END_GAME' });
    }
  }, [state.snake.length, state.gameOver]);

  // Word validation - check for valid words starting from any position in the snake
  useEffect(() => {
    // Skip if wordValidator isn't loaded or we don't have enough letters
    if (!wordValidator || state.collectedLetters.length < 3) {
      return;
    }

    // Check all possible substrings of the collected letters for valid words
    const letters = state.collectedLetters;
    console.log('Checking for valid words in collected letters:', letters.join(''));
    
    // Start from the head of the snake (most recent letters first)
    // This ensures we check words as they're formed from the head
    for (let length = 3; length <= letters.length; length++) {
      // Get the most recent 'length' letters (from the head of the snake)
      const subLetters = letters.slice(0, length);
      const word = subLetters.join('').toUpperCase();
      
      // Check if this substring forms a valid word
      if (wordValidator.isValidWord(word)) {
        console.log('Valid word found at head:', word);
        
        // Create indices array for the word segments (from head)
        const indices = Array.from({ length: subLetters.length }, (_, i) => i);
        
        // Create particles for visual effect
        if (gameAreaRef.current) {
          const snakeElements = gameAreaRef.current.querySelectorAll('.snake-segment');
          const wordSegments = Array.from(snakeElements).slice(0, length);
          
          // Apply tetris disappearing animation to segments
          wordSegments.forEach(segment => {
            // Add the disappearing-word class to trigger the animation
            segment.classList.add('disappearing-word');
            
            // Create particle effect
            const rect = segment.getBoundingClientRect();
            createParticles(rect.left + rect.width / 2, rect.top + rect.height / 2, 'success');
          });
          
          // Play sound effect
          playSound('wordFormed');
        }
        
        // Process the word
        dispatch({
          type: 'PROCESS_WORD',
          payload: { word, indices }
        });
        
        // Exit after finding the first valid word
        return;
      }
    }
    
    // If no word found from the head, check for words anywhere in the snake
    for (let startIdx = 1; startIdx < letters.length - 2; startIdx++) {
      for (let endIdx = letters.length; endIdx > startIdx + 2; endIdx--) {
        // Extract the substring
        const subLetters = letters.slice(startIdx, endIdx);
        const word = subLetters.join('').toUpperCase();
        
        // Check if this substring forms a valid word
        if (wordValidator.isValidWord(word)) {
          console.log('Valid word found in middle:', word);
          
          // Create indices array for the word segments
          const indices = Array.from({ length: subLetters.length }, (_, i) => i + startIdx);
          
          // Create particles for visual effect
          if (gameAreaRef.current) {
            const snakeElements = gameAreaRef.current.querySelectorAll('.snake-segment');
            const wordSegments = Array.from(snakeElements).slice(startIdx, startIdx + subLetters.length);
            
            wordSegments.forEach(segment => {
              const rect = segment.getBoundingClientRect();
              createParticles(rect.left + rect.width / 2, rect.top + rect.height / 2, 'success');
            });
          }
          
          // Process the word
          dispatch({
            type: 'PROCESS_WORD',
            payload: { word, indices }
          });
          
          // Exit after finding the first valid word
          return;
        }
      }
    }
  }, [state.collectedLetters, wordValidator]);

  // Game loop for snake movement
  const moveSnake = useCallback(() => {
    dispatch({ type: 'MOVE_SNAKE' });
  }, [dispatch]);

  // Main game loop - handles snake movement and collision detection
  useGameLoop(
    () => {
      if (state.isPaused || state.countdownActive || state.gameOver || !state.isGameStarted) return;
      moveSnake();
    },
    GAME_CONFIG.SNAKE_SPEED,
    0, // Remove initial delay to start moving immediately after countdown
    [state.isPaused, state.countdownActive, state.gameOver, state.isGameStarted, state.direction]
  );

  const handlePauseResume = () => {
    if (state.gameOver) return;
    
    if (state.isPaused) {
      // If paused, start countdown and then unpause
      setShowRules(false);
      dispatch({ type: 'SET_COUNTDOWN', payload: true });
    } else {
      // If playing, pause the game and show rules
      dispatch({ type: 'TOGGLE_PAUSE' });
      setShowRules(true);
    }
  };

  // Handle restart
  const handleRestart = () => {
    dispatch({ type: 'RESET_GAME' });
    setShowRules(true);
  };

  // Render game grid cells
  const renderGrid = () => {
    const cells = [];
    for (let y = 0; y < GAME_CONFIG.GRID_SIZE; y++) {
      for (let x = 0; x < GAME_CONFIG.GRID_SIZE; x++) {
        const isSnakeCell = state.snake.some(segment => segment.x === x && segment.y === y);
        const foodItem = state.foods.find(food => food.position.x === x && food.position.y === y);
        
        const cellKey = `cell-${x}-${y}`;
        // Use CSS grid for exact positioning
        const cellStyle = {
          gridColumnStart: x + 1,
          gridRowStart: y + 1
        };
        
        if (isSnakeCell) {
          const segmentIndex = state.snake.findIndex(segment => segment.x === x && segment.y === y);
          const isHead = segmentIndex === 0;
          const letter = state.collectedLetters[segmentIndex] || '';
          
          cells.push(
            <div
              key={cellKey}
              className={`snake-segment ${isHead ? 'snake-head' : ''}`}
              style={cellStyle}
            >
              {letter}
            </div>
          );
        } else if (foodItem) {
          const isVowel = /[aeiou]/i.test(foodItem.letter);
          
          // Calculate absolute position for food container
          // Use percentage-based positioning with full size to match snake segments
          const foodContainerStyle = {
            left: `${x * 100 / GAME_CONFIG.GRID_SIZE}%`,
            top: `${y * 100 / GAME_CONFIG.GRID_SIZE}%`,
            width: `${100 / GAME_CONFIG.GRID_SIZE}%`,
            height: `${100 / GAME_CONFIG.GRID_SIZE}%`,
          };
          
          cells.push(
            <div
              key={cellKey}
              className="food-container"
              style={foodContainerStyle}
              data-testid={`food-${x}-${y}`}
            >
              <div
                className={`food ${isVowel ? 'vowel' : 'consonant'}`}
                style={{ width: '100%', height: '100%' }}
                data-testid={`food-letter-${foodItem.letter}`}
              >
                {foodItem.letter}
              </div>
            </div>
          );
        }
      }
    }
    return cells;
  };

  // Render game controls for mobile
  const renderControls = () => {
    return (
      <div className="controls in-game">
        <button 
          className="control-btn up" 
          onClick={() => dispatch({ type: 'CHANGE_DIRECTION', payload: Direction.UP })}
        >
          <span style={{ fontSize: '1.2em' }}>▲</span>
        </button>
        <div className="horizontal-controls">
          <button 
            className="control-btn left" 
            onClick={() => dispatch({ type: 'CHANGE_DIRECTION', payload: Direction.LEFT })}
          >
            <span style={{ fontSize: '1.2em' }}>◄</span>
          </button>
          <button 
            className="control-btn right" 
            onClick={() => dispatch({ type: 'CHANGE_DIRECTION', payload: Direction.RIGHT })}
          >
            <span style={{ fontSize: '1.2em' }}>►</span>
          </button>
        </div>
        <button 
          className="control-btn down" 
          onClick={() => dispatch({ type: 'CHANGE_DIRECTION', payload: Direction.DOWN })}
        >
          <span style={{ fontSize: '1.2em' }}>▼</span>
        </button>
      </div>
    );
  };

  return (
    <div className="game-container">
      {/* Game title - only show when not in rules or countdown */}
      {!showRules && !state.countdownActive && (
        <h1 className="game-title">
          Word<span className="snake-title-highlight">Snake</span>
        </h1>
      )}

      <div 
        className="game-area"
        ref={gameAreaRef}
        style={{
          gridTemplateColumns: `repeat(${GAME_CONFIG.GRID_SIZE}, 1fr)`,
          gridTemplateRows: `repeat(${GAME_CONFIG.GRID_SIZE}, 1fr)`
        }}
      >
        {/* Pause button inside game area */}
        {!showRules && !state.countdownActive && !state.gameOver && (
          <button 
            className="pause-button in-game"
            onClick={handlePauseResume}
          >
            {state.isPaused ? '▶' : '⏸'}
          </button>
        )}
        {renderGrid()}
        
        {/* Overlay for rules */}
        {showRules && (
          <div className="rules-overlay">
            <h2>WordSnake Rules</h2>
            <ul>
              <li>Use arrow keys to move the snake</li>
              <li>Collect letters to form words</li>
              <li>Valid words will disappear from the snake</li>
              <li>Game ends if snake exceeds {GAME_CONFIG.MAX_SNAKE_LETTERS} letters</li>
              <li>Try to collect as many words as possible!</li>
            </ul>
            <button onClick={handlePauseResume}>
              {state.isGameStarted ? 'Resume' : 'Start'}
            </button>
          </div>
        )}
        
        {/* Countdown overlay */}
        {state.countdownActive && (
          <div className="countdown-overlay">
            <div className="countdown">{countdownValue}</div>
          </div>
        )}
        
        {/* Game over overlay */}
        {state.gameOver && (
          <div className="gameover-overlay">
            <div className="gameover-content">
              <h2>Game Over!</h2>
              <div className="final-score">
                <p>Score: {state.score}</p>
                <p>Words Collected: {state.wordsCollected}</p>
                <p>Letters Collected: {state.lettersCollected}</p>
                <p>Time Survived: {state.gameTime}s</p>
              </div>
              <button onClick={handleRestart} className="play-again-button">Play Again</button>
            </div>
          </div>
        )}

        {/* Touch controls for mobile */}
        {!state.isPaused && !state.countdownActive && !state.gameOver && renderControls()}
      </div>
      
      {/* Score bar at bottom - only show during active gameplay */}
      {!showRules && !state.countdownActive && !state.gameOver && (
        <div className="game-info">
          <div className="score-bar">
            <div className="score-metric">
              <span className="metric-label">Score</span>
              <span className="metric-value">{state.score}</span>
            </div>
            <div className="score-metric">
              <span className="metric-label">Words</span>
              <span className="metric-value">{state.wordsCollected}</span>
            </div>
            <div className="score-metric">
              <span className="metric-label">Letters</span>
              <span className="metric-value">{state.lettersCollected}</span>
            </div>
            <div className="score-metric">
              <span className="metric-label">Time</span>
              <span className="metric-value">{state.gameTime}s</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GameBoard;
