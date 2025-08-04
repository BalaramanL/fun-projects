
import { GAME_CONFIG } from './constants';

export interface Position {
  x: number;
  y: number;
}

export function getRandomPosition(maxX: number, maxY: number, avoidPositions: Position[] = []): Position {
  let position: Position;
  let attempts = 0;
  const maxAttempts = 100; // Prevent infinite loop

  do {
    position = {
      x: Math.floor(Math.random() * maxX),
      y: Math.floor(Math.random() * maxY),
    };
    attempts++;
  } while (
    attempts < maxAttempts &&
    avoidPositions.some(pos => pos.x === position.x && pos.y === position.y)
  );

  return position;
}

// Generate a random letter with proper vowel distribution
export function getRandomLetter(): string {
  const vowels = ['A', 'E', 'I', 'O', 'U'];
  const consonants = [
    'B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M',
    'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z'
  ];
  
  // Weight common letters higher for better word formation
  const commonConsonants = ['R', 'S', 'T', 'N', 'L'];
  const weightedConsonants = [...consonants, ...commonConsonants];
  
  const isVowel = Math.random() < GAME_CONFIG.VOWEL_PROBABILITY;
  
  if (isVowel) {
    // Weight common vowels higher
    const weightedVowels = ['E', 'A', 'E', 'I', 'O', 'E', 'A', 'U'];
    return weightedVowels[Math.floor(Math.random() * weightedVowels.length)];
  } else {
    return weightedConsonants[Math.floor(Math.random() * weightedConsonants.length)];
  }
}

// Animation helper functions
export function fadeIn(element: HTMLElement, duration: number): Promise<void> {
  return new Promise((resolve) => {
    element.style.opacity = '0';
    element.style.transition = `opacity ${duration}ms ease-in-out`;
    
    setTimeout(() => {
      element.style.opacity = '1';
      setTimeout(resolve, duration);
    }, 10);
  });
}

export function fadeOut(element: HTMLElement, duration: number): Promise<void> {
  return new Promise((resolve) => {
    element.style.opacity = '1';
    element.style.transition = `opacity ${duration}ms ease-in-out`;
    
    setTimeout(() => {
      element.style.opacity = '0';
      setTimeout(resolve, duration);
    }, 10);
  });
}

export function createParticles(x: number, y: number, color: string, count: number = 10): void {
  const container = document.querySelector('.game-board');
  if (!container) return;
  
  for (let i = 0; i < count; i++) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    particle.style.position = 'absolute';
    particle.style.width = '5px';
    particle.style.height = '5px';
    particle.style.backgroundColor = color;
    particle.style.borderRadius = '50%';
    particle.style.left = `${x}px`;
    particle.style.top = `${y}px`;
    particle.style.pointerEvents = 'none';
    
    // Random direction
    const angle = Math.random() * Math.PI * 2;
    const speed = 1 + Math.random() * 3;
    const vx = Math.cos(angle) * speed;
    const vy = Math.sin(angle) * speed;
    
    container.appendChild(particle);
    
    // Animate
    let frameCount = 0;
    const maxFrames = 30 + Math.floor(Math.random() * 20);
    
    const animate = () => {
      if (frameCount >= maxFrames) {
        container.removeChild(particle);
        return;
      }
      
      const left = parseFloat(particle.style.left);
      const top = parseFloat(particle.style.top);
      
      particle.style.left = `${left + vx}px`;
      particle.style.top = `${top + vy}px`;
      particle.style.opacity = `${1 - frameCount / maxFrames}`;
      
      frameCount++;
      requestAnimationFrame(animate);
    };
    
    requestAnimationFrame(animate);
  }
}
