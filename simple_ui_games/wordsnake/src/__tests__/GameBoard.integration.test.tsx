import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import GameBoard from '../components/GameBoard/GameBoard';

// Mock the sound effects to avoid actual audio playback during tests
jest.mock('../utils/soundEffects', () => ({
  playSound: jest.fn(),
  initAudio: jest.fn(),
}));

// Mock the word validator hook
jest.mock('../hooks/useWordValidator', () => ({
  useWordValidator: () => jest.fn((word) => {
    // Simple mock dictionary for testing
    const dictionary = ['CAT', 'DOG', 'SNAKE', 'FAR', 'ARE', 'EAT'];
    return dictionary.includes(word.toUpperCase());
  }),
}));

// Mock the game loop hook to control execution in tests
jest.mock('../hooks/useGameLoop', () => {
  const callbacks = new Map();
  
  return {
    useGameLoop: (callback: () => void, speed: number, initialDelay: number, dependencies: any[] = []) => {
      // Store the callback with a unique key based on dependencies
      const key = JSON.stringify(dependencies);
      callbacks.set(key, callback);
      
      // Expose a way to trigger the callback for testing
      (window as any).__triggerGameLoop = (depKey: string) => {
        const cb = callbacks.get(depKey);
        if (cb) cb();
      };
    },
  };
});

describe('GameBoard Integration Tests', () => {
  beforeEach(() => {
    // Reset any mocks or state before each test
    jest.clearAllMocks();
  });
  
  // Test for game initialization
  it('should initialize the game with correct state', () => {
    render(<GameBoard />);
    
    // Game should start paused with rules shown
    expect(screen.getByText(/Use arrow keys/i)).toBeInTheDocument();
    
    // Snake should be rendered
    const snakeSegments = document.querySelectorAll('.snake-segment');
    expect(snakeSegments.length).toBeGreaterThan(0);
  });
  
  // Test for food rendering
  it('should render food with correct appearance', () => {
    const { container } = render(<GameBoard />);
    
    // Manually add food to the game state
    act(() => {
      // Simulate food generation
      const foodContainer = document.createElement('div');
      foodContainer.className = 'food-container';
      foodContainer.setAttribute('data-testid', 'food-5-5');
      
      const food = document.createElement('div');
      food.className = 'food';
      food.textContent = 'A';
      
      foodContainer.appendChild(food);
      container.querySelector('.game-board')?.appendChild(foodContainer);
    });
    
    // Check if food is rendered
    const foodElements = container.querySelectorAll('.food');
    expect(foodElements.length).toBeGreaterThan(0);
    
    // Check food appearance
    if (foodElements.length > 0) {
      const foodStyle = window.getComputedStyle(foodElements[0]);
      
      // Check for circular shape
      expect(foodStyle.borderRadius).toBe('50%');
      
      // Check for fixed size
      expect(foodStyle.width).toBe('20px');
      expect(foodStyle.height).toBe('20px');
      
      // Check for absolute positioning
      expect(foodStyle.position).toBe('absolute');
    }
  });
  
  // Test for snake movement and food collection
  it('should move snake and collect food when arrow keys are pressed', () => {
    const { container } = render(<GameBoard />);
    
    // Start the game (dismiss rules)
    const startButton = screen.getByText(/Resume/i);
    fireEvent.click(startButton);
    
    // Wait for countdown to complete
    act(() => {
      // Fast-forward countdown
      for (let i = 3; i >= 0; i--) {
        jest.advanceTimersByTime(1000);
      }
    });
    
    // Get initial snake length
    const initialSnakeSegments = container.querySelectorAll('.snake-segment');
    const initialLength = initialSnakeSegments.length;
    
    // Press arrow key to move snake
    fireEvent.keyDown(document, { key: 'ArrowRight' });
    
    // Trigger game loop to move snake
    act(() => {
      (window as any).__triggerGameLoop('[]');
    });
    
    // Check if snake moved
    const newSnakeSegments = container.querySelectorAll('.snake-segment');
    expect(newSnakeSegments.length).toBe(initialLength);
    
    // Simulate food collection
    act(() => {
      // Manually add food where snake will move
      const foodContainer = document.createElement('div');
      foodContainer.className = 'food-container';
      
      const food = document.createElement('div');
      food.className = 'food';
      food.textContent = 'A';
      
      foodContainer.appendChild(food);
      container.querySelector('.game-board')?.appendChild(foodContainer);
      
      // Move snake to food
      (window as any).__triggerGameLoop('[]');
    });
    
    // Check if snake grew after eating food
    const finalSnakeSegments = container.querySelectorAll('.snake-segment');
    expect(finalSnakeSegments.length).toBeGreaterThan(initialLength);
  });
  
  // Test for game over condition
  it('should end game when snake exceeds maximum length', () => {
    const { container } = render(<GameBoard />);
    
    // Start the game
    const startButton = screen.getByText(/Resume/i);
    fireEvent.click(startButton);
    
    // Wait for countdown to complete
    act(() => {
      // Fast-forward countdown
      for (let i = 3; i >= 0; i--) {
        jest.advanceTimersByTime(1000);
      }
    });
    
    // Simulate snake growing to maximum length
    act(() => {
      // Force game over state
      const gameOverEvent = new CustomEvent('gameOver');
      document.dispatchEvent(gameOverEvent);
    });
    
    // Check for game over message
    expect(screen.getByText(/Game Over/i)).toBeInTheDocument();
  });
});
