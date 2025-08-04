
import React from 'react';
import '../../styles/GameStyles.css';

// No need to import Direction as it's not used in this component

interface ControlPanelProps {
  isGameOver: boolean;
  onRestart: () => void;
}

const ControlPanel: React.FC<ControlPanelProps> = ({ isGameOver, onRestart }) => {
  return (
    <div className="control-panel">
      {isGameOver ? (
        <button className="restart-button" onClick={onRestart}>Play Again</button>
      ) : (
        <div className="controls-info">
          <p>Use arrow keys or WASD to move</p>
          <p>Collect letters to form words</p>
          <p>Valid words will disappear from your snake</p>
        </div>
      )}
    </div>
  );
};

export default ControlPanel;
