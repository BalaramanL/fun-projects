# AlphaSnake

AlphaSnake is a modern, responsive implementation of the classic Snake game with an educational twist - players must collect letters of the alphabet in order from A to Z.

![AlphaSnake Game](https://github.com/BalaramanL/fun-projects/blob/main/simple_ui_games/alphasnake/screenshot.png)

## Features

- Responsive design that works on desktop and mobile devices
- Touch controls for mobile play
- Keyboard controls (arrow keys or WASD) for desktop play
- Multiple difficulty levels affecting game speed and food placement
- 8-bit style background music and sound effects
- Adaptive grid size based on screen dimensions
- Score tracking and next letter display
- Game over and victory screens

## How to Play

1. Open `index.html` in any modern web browser
2. Click anywhere or press any key to start the game
3. Control the snake using:
   - **Desktop**: Arrow keys or WASD keys
   - **Mobile**: Touch buttons or swipe on the game canvas
4. Collect letters in alphabetical order from A to Z
5. Avoid collisions with walls and the snake's own body
6. Adjust difficulty using the slider before starting the game

## Code Structure and Flow

### HTML Structure

The game is built as a single HTML file with embedded CSS and JavaScript. The HTML structure consists of:

1. **Game Container**: Houses the main game elements
2. **Canvas**: Where the game is rendered
3. **UI Elements**: Score display, next letter indicator, and difficulty controls
4. **Touch Controls**: Directional buttons for mobile play
5. **Game Over Screen**: Displays when the game ends

### CSS Styling

The CSS provides:
- Responsive layouts for different screen sizes
- Touch button styling with visual feedback
- Game container positioning and dimensions
- Adaptive canvas sizing
- Mobile-friendly UI elements

### JavaScript Game Logic

#### Initialization

1. `initGame()`: Sets up the initial game state
   - Adjusts canvas size based on screen dimensions
   - Generates initial food
   - Sets up event listeners
   - Initializes UI elements

2. `startGame()`: Triggered by first user interaction
   - Initializes audio context
   - Starts game loop
   - Plays background music
   - Sets up keyboard controls

#### Game Loop

The main game loop runs at intervals determined by the difficulty level:

1. `updateGame()`: Called on each tick of the game loop
   - Processes queued direction changes
   - Updates snake position
   - Checks for collisions (walls, self)
   - Checks for food collection
   - Updates score and generates new food if needed

2. `drawGame()`: Renders the current game state
   - Clears the canvas
   - Draws the snake with gradient coloring
   - Draws the food with the current letter

#### Input Handling

1. `handleKeyDown()`: Processes keyboard input
   - Maps arrow keys and WASD to directions
   - Starts game if not running
   - Calls direction change handler

2. `handleDirectionChange()`: Unified handler for all direction inputs
   - Validates direction changes (can't reverse directly)
   - Allows any direction change before first food collection
   - Queues changes that can't be applied immediately
   - Throttles rapid inputs to prevent speed increases

3. Touch Controls: Handle mobile input
   - Direction buttons with visual feedback
   - Swipe detection on the canvas
   - Prevent scrolling while playing

#### Audio System

1. `initAudio()`: Sets up Web Audio API context
   - Created on first user interaction to comply with browser policies
   - Handles suspended state resumption

2. `playBackgroundMusic()`: Generates simple 8-bit style music
   - Uses oscillators and gain nodes
   - Creates a looping melody pattern

3. Sound Effects: For game events
   - Food collection
   - Game over
   - Victory

#### Game State Management

1. `restartGame()`: Resets the game after game over
   - Clears existing game loop and audio
   - Resets snake position, direction, and score
   - Generates new food
   - Starts new game loop with proper timing

2. `gameOver()`: Handles end-of-game conditions
   - Stops game loop and audio
   - Displays appropriate message based on win/lose condition
   - Re-enables difficulty adjustment

## Adaptive Features

1. **Responsive Design**:
   - Canvas size adjusts based on screen width
   - UI elements reposition for mobile devices
   - Touch controls appear only on mobile/touch devices

2. **Grid Size Adaptation**:
   - Smaller grid size on mobile for better control
   - Larger grid on desktop for more detailed gameplay
   - Prevents premature boundary collisions on small screens

3. **Difficulty Settings**:
   - Affects game speed
   - Controls food placement (keeps food away from edges on easier levels)
   - Can only be changed before game starts

## Nuances and Edge Cases

The game handles several edge cases and potential issues:

### 1. Direction Change Handling

- **Problem**: Snake speed increases if same direction button is pressed repeatedly on touch
- **Solution**: Throttled direction changes to once every 100ms to prevent speed issues

- **Problem**: Cannot change direction before capturing first letter
- **Solution**: Special case for score === 0 that allows any direction change at the start

- **Problem**: Direction not changing when opening HTML file directly
- **Solution**: Added persistent keydown event listener in startGame function

### 2. Game State Reset

- **Problem**: Next letter display is not reset to 'A' after 'Play Again' until food is eaten
- **Solution**: Reset score before generating food and update UI immediately

- **Problem**: Snake speed increases automatically after 'Play again' on mobile
- **Solution**: Properly clear and reset game loop with null reference

### 3. Movement and Collision Detection

- **Problem**: Movement granularity/grid size does not adapt to screen size
- **Solution**: Dynamic grid size based on screen width (15px, 18px, or 20px)

- **Problem**: Jittery movement on desktop/keyboard controls
- **Solution**: Implemented direction queue system to improve responsiveness

### 4. Audio Handling

- **Problem**: Background music does not play on first game start
- **Solution**: Proper audio context initialization on user interaction and explicit resuming

- **Problem**: Jittery movement after restart related to audio issues
- **Solution**: Better audio resource management with proper cleanup

### 5. Mobile Optimization

- **Problem**: Touch events causing unwanted scrolling
- **Solution**: Added preventDefault() and passive: false to touch event listeners

- **Problem**: Food spawning near edges on small screens making it hard to collect
- **Solution**: Added margin to food generation based on difficulty level

## Browser Compatibility

AlphaSnake works on all modern browsers including:
- Chrome
- Firefox
- Safari
- Edge

Mobile support includes iOS and Android devices through responsive design and touch controls.

## License

This project is licensed under a modified GNU GPL v3.0 License - see the [LICENSE.md](LICENSE.md) file for details.
Commercial use requires explicit permission from the author.

## Author

Developed by [BalaramanL](https://github.com/BalaramanL/fun-projects/tree/main/simple_ui_games/alphasnake)
