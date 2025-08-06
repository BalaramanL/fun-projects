// Using JSX syntax which implicitly uses React
import './App.css';
import './styles/GameStyles.css';
// Import the GameBoard component
import GameBoard from './components/GameBoard/GameBoard';

function App() {
  return (
    <div className="App">
      <h1 className="game-title">Word<span className="title-accent">Snake</span></h1>
      <p className="game-subtitle">Collect letters to form words!</p>
      <GameBoard />
    </div>
  );
}

export default App;