// 8-bit Sound effects utility for WordSnake game using Web Audio API

// Initialize audio context lazily to avoid autoplay restrictions
let audioContext: AudioContext | null = null;

// Sound types
export type SoundType = 'eat' | 'turn' | 'wordFormed' | 'gameOver';

// Initialize audio context on first user interaction
const getAudioContext = (): AudioContext => {
  if (!audioContext) {
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  return audioContext;
};

// Generate 8-bit eat sound (short high beep)
const generateEatSound = (context: AudioContext): void => {
  const oscillator = context.createOscillator();
  const gainNode = context.createGain();
  
  oscillator.type = 'square'; // Square wave for 8-bit sound
  oscillator.frequency.setValueAtTime(800, context.currentTime); // Higher pitch
  oscillator.frequency.exponentialRampToValueAtTime(1200, context.currentTime + 0.1);
  
  gainNode.gain.setValueAtTime(0.3, context.currentTime);
  gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.1);
  
  oscillator.connect(gainNode);
  gainNode.connect(context.destination);
  
  oscillator.start();
  oscillator.stop(context.currentTime + 0.1);
};

// Generate 8-bit turn sound (quick low beep)
const generateTurnSound = (context: AudioContext): void => {
  const oscillator = context.createOscillator();
  const gainNode = context.createGain();
  
  oscillator.type = 'square';
  oscillator.frequency.setValueAtTime(300, context.currentTime);
  oscillator.frequency.exponentialRampToValueAtTime(150, context.currentTime + 0.08);
  
  gainNode.gain.setValueAtTime(0.2, context.currentTime);
  gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.08);
  
  oscillator.connect(gainNode);
  gainNode.connect(context.destination);
  
  oscillator.start();
  oscillator.stop(context.currentTime + 0.08);
};

// Generate 8-bit word formed sound (ascending notes)
const generateWordFormedSound = (context: AudioContext): void => {
  const notes = [400, 500, 600, 700, 800];
  const noteDuration = 0.08;
  
  notes.forEach((frequency, index) => {
    const oscillator = context.createOscillator();
    const gainNode = context.createGain();
    
    oscillator.type = 'square';
    oscillator.frequency.setValueAtTime(frequency, context.currentTime + index * noteDuration);
    
    gainNode.gain.setValueAtTime(0, context.currentTime + index * noteDuration);
    gainNode.gain.linearRampToValueAtTime(0.3, context.currentTime + index * noteDuration + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + (index + 1) * noteDuration);
    
    oscillator.connect(gainNode);
    gainNode.connect(context.destination);
    
    oscillator.start(context.currentTime + index * noteDuration);
    oscillator.stop(context.currentTime + (index + 1) * noteDuration);
  });
};

// Generate 8-bit game over sound (descending notes)
const generateGameOverSound = (context: AudioContext): void => {
  const notes = [600, 500, 400, 300, 200, 150];
  const noteDuration = 0.15;
  
  notes.forEach((frequency, index) => {
    const oscillator = context.createOscillator();
    const gainNode = context.createGain();
    
    oscillator.type = 'sawtooth'; // More complex waveform for dramatic effect
    oscillator.frequency.setValueAtTime(frequency, context.currentTime + index * noteDuration);
    
    gainNode.gain.setValueAtTime(0, context.currentTime + index * noteDuration);
    gainNode.gain.linearRampToValueAtTime(0.3, context.currentTime + index * noteDuration + 0.02);
    gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + (index + 1) * noteDuration);
    
    oscillator.connect(gainNode);
    gainNode.connect(context.destination);
    
    oscillator.start(context.currentTime + index * noteDuration);
    oscillator.stop(context.currentTime + (index + 1) * noteDuration);
  });
};

// Play a sound effect
export const playSound = (soundType: SoundType): void => {
  try {
    const context = getAudioContext();
    
    switch (soundType) {
      case 'eat':
        generateEatSound(context);
        break;
      case 'turn':
        generateTurnSound(context);
        break;
      case 'wordFormed':
        generateWordFormedSound(context);
        break;
      case 'gameOver':
        generateGameOverSound(context);
        break;
      default:
        console.warn(`Unknown sound type: ${soundType}`);
    }
  } catch (error) {
    console.error(`Error playing sound ${soundType}:`, error);
  }
};

// Initialize audio context on first user interaction
export const initAudio = (): void => {
  getAudioContext();
  // Play a silent sound to initialize audio context
  const silentOscillator = audioContext!.createOscillator();
  const silentGain = audioContext!.createGain();
  silentGain.gain.value = 0.001;
  silentOscillator.connect(silentGain);
  silentGain.connect(audioContext!.destination);
  silentOscillator.start();
  silentOscillator.stop(audioContext!.currentTime + 0.001);
};
