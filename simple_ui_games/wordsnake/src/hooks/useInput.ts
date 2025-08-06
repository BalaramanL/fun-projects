
import { useEffect, useState } from 'react';

export enum Direction {
  UP = 'UP',
  DOWN = 'DOWN',
  LEFT = 'LEFT',
  RIGHT = 'RIGHT'
}

export function useInput() {
  const [direction, setDirection] = useState<Direction>(Direction.RIGHT);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowUp':
        case 'w':
          setDirection(Direction.UP);
          break;
        case 'ArrowDown':
        case 's':
          setDirection(Direction.DOWN);
          break;
        case 'ArrowLeft':
        case 'a':
          setDirection(Direction.LEFT);
          break;
        case 'ArrowRight':
        case 'd':
          setDirection(Direction.RIGHT);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  return direction;
}
