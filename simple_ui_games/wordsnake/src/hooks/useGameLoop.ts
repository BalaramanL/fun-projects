
import { useEffect, useRef } from 'react';

export function useGameLoop(
  callback: () => void,
  speed: number = 0,
  initialDelay: number = 0
) {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    // Don't start the loop if speed is 0
    if (speed <= 0) return;

    let timeoutId: NodeJS.Timeout;
    
    // Initial delay before starting the game loop
    const startLoop = () => {
      timeoutId = setTimeout(() => {
        callbackRef.current();
        timeoutId = setTimeout(startLoop, speed);
      }, speed);
    };

    // Apply initial delay if specified
    const initialTimeoutId = setTimeout(() => {
      startLoop();
    }, initialDelay);

    // Cleanup function
    return () => {
      clearTimeout(initialTimeoutId);
      clearTimeout(timeoutId);
    };
  }, [speed, initialDelay]);
}
