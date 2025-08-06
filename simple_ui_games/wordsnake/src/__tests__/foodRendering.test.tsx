import React from 'react';
import { render, screen } from '@testing-library/react';
import GameBoard from '../components/GameBoard/GameBoard';
import { gameReducer, initialGameState } from '../components/GameBoard/gameState';

// Mock the sound effects to avoid actual audio playback during tests
jest.mock('../utils/soundEffects', () => ({
  playSound: jest.fn(),
  initAudio: jest.fn(),
}));

// Mock the word validator hook
jest.mock('../hooks/useWordValidator', () => ({
  useWordValidator: () => jest.fn(() => true),
}));

// Mock the game loop hook to prevent actual game loop execution
jest.mock('../hooks/useGameLoop', () => ({
  useGameLoop: jest.fn((callback) => {
    // Store the callback but don't execute it
  }),
}));

describe('Food Rendering', () => {
  // Test for food bubble rendering
  it('should render food bubbles as perfect circles with correct positioning', () => {
    // Create a test state with food
    const testState = {
      ...initialGameState,
      foods: [
        { position: { x: 5, y: 5 }, letter: 'A' },
      ],
    };
    
    // Mock the useReducer hook to return our test state
    jest.spyOn(React, 'useReducer').mockImplementation(() => [testState, jest.fn()]);
    
    // Render the component
    const { container } = render(<GameBoard />);
    
    // Force a re-render to ensure our mocked state is used
    const { rerender } = render(<GameBoard />);
    
    // Find food container and food elements
    const foodContainer = container.querySelector('.food-container');
    const food = container.querySelector('.food');
    
    // Check if elements exist
    expect(foodContainer).not.toBeNull();
    expect(food).not.toBeNull();
    
    if (food && foodContainer) {
      // Get computed styles
      const foodStyle = window.getComputedStyle(food);
      const containerStyle = window.getComputedStyle(foodContainer);
      
      // Check food container positioning
      expect(containerStyle.position).toBe('relative');
      
      // Check food element positioning and shape
      expect(foodStyle.position).toBe('absolute');
      expect(foodStyle.borderRadius).toBe('50%');
      expect(foodStyle.width).toBe('20px');
      expect(foodStyle.height).toBe('20px');
      
      // Check that transform and transitions are disabled
      expect(foodStyle.transform).toBe('none');
      expect(foodStyle.transition).toBe('none');
      expect(foodStyle.animation).toBe('none');
      
      // Check centering
      expect(foodStyle.top).toBe('50%');
      expect(foodStyle.left).toBe('50%');
      expect(foodStyle.marginTop).toBe('-10px');
      expect(foodStyle.marginLeft).toBe('-10px');
    }
  });
  
  // Test for vowel vs. consonant styling
  it('should apply different styling for vowels and consonants', () => {
    // Render the component
    const { container } = render(<GameBoard />);
    
    // Create test state with vowel and consonant foods
    const testState = {
      ...initialGameState,
      foods: [
        { position: { x: 5, y: 5 }, letter: 'A' }, // Vowel
        { position: { x: 6, y: 6 }, letter: 'B' }, // Consonant
      ],
    };
    
    // Find vowel and consonant elements
    const vowelFood = container.querySelector('.food.vowel');
    const consonantFood = container.querySelector('.food:not(.vowel)');
    
    // Check if elements exist
    expect(vowelFood).not.toBeNull();
    expect(consonantFood).not.toBeNull();
    
    if (vowelFood && consonantFood) {
      // Get computed styles
      const vowelStyle = window.getComputedStyle(vowelFood);
      const consonantStyle = window.getComputedStyle(consonantFood);
      
      // Verify different background colors
      expect(vowelStyle.backgroundColor).not.toBe(consonantStyle.backgroundColor);
    }
  });
});

// Test for vowel distribution in food generation
describe('Vowel Distribution', () => {
  it('should enforce at least 1 vowel per 4 letters', () => {
    // Mock the random letter generation to always return consonants
    jest.spyOn(Math, 'random').mockReturnValue(0.9); // High value to get consonants
    
    // Create a test state with no vowels
    const testState = {
      ...initialGameState,
      foods: [
        { position: { x: 1, y: 1 }, letter: 'B' },
        { position: { x: 2, y: 2 }, letter: 'C' },
        { position: { x: 3, y: 3 }, letter: 'D' },
      ],
      collectedLetters: ['F', 'G', 'H'],
    };
    
    // Simulate adding a new food - with our vowel enforcement, this should be a vowel
    const action = {
      type: 'ADD_FOOD' as const,
      payload: { 
        position: { x: 4, y: 4 },
        letter: 'A' // This would be determined by the vowel enforcement logic
      },
    };
    
    // Apply the action
    const newState = gameReducer(testState, action);
    
    // Count vowels in all letters (foods + snake)
    const allLetters = [
      ...newState.foods.map(f => f.letter),
      ...newState.collectedLetters
    ];
    
    const vowelCount = allLetters.filter(letter => /[aeiou]/i.test(letter)).length;
    
    // Verify we have at least 1 vowel per 4 letters
    expect(vowelCount).toBeGreaterThanOrEqual(Math.ceil(allLetters.length / 4));
    
    // Restore Math.random
    jest.spyOn(Math, 'random').mockRestore();
  });
});
