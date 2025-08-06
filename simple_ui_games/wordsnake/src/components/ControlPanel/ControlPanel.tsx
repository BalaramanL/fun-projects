
import React from 'react';
import '../../styles/GameStyles.css';

interface ControlPanelProps {
  isGameOver: boolean;
  isPaused?: boolean;
  onRestart: () => void;
  onPause?: () => void;
}

const ControlPanel: React.FC<ControlPanelProps> = ({ isGameOver, onRestart, onPause }) => {
  return (
    <div className="control-panel">
      {isGameOver ? (
        <button className="restart-button" onClick={onRestart}>Play Again</button>
      ) : (
        <div className="controls-info">
          <p>Use arrow keys or WASD to move</p>
          <p>Collect letters to form words</p>
          <p>Valid words will disappear from your snake</p>
          {onPause && <p>Press P or ESC to pause</p>}
        </div>
      )}
    </div>
  );
};

export default ControlPanel;
