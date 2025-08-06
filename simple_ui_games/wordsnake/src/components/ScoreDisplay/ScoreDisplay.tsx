
import React from 'react';
import '../../styles/GameStyles.css';

interface ScoreDisplayProps {
  score: number;
  time: number;
  wordsCollected: number;
  currentLetters?: string[];
}

const ScoreDisplay: React.FC<ScoreDisplayProps> = ({ score, time, wordsCollected, currentLetters = [] }) => {
  return (
    <div className="score-display">
      <div className="score-item">
        <span className="score-label">Score:</span>
        <span className="score-value">{score}</span>
      </div>
      <div className="score-item">
        <span className="score-label">Words:</span>
        <span className="score-value">{wordsCollected}</span>
      </div>
      <div className="score-item">
        <span className="score-label">Time:</span>
        <span className="score-value">{time}s</span>
      </div>
      {currentLetters.length > 0 && (
        <div className="current-letters">
          {currentLetters.join('')}
        </div>
      )}
    </div>
  );
};

export default ScoreDisplay;
