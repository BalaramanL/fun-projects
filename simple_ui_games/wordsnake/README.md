# Word Snake Game

This is a modern twist on the classic Snake game where players collect alphabet letters to form English words. The game combines traditional snake mechanics with word formation challenges, requiring strategic movement to create valid dictionary words while avoiding death conditions.

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd word-snake-game

# Install dependencies
npm install

# Generate dictionary file (required for first run)
npm run generate-dict

# Start development server
npm run dev
```

## Prerequisites

### System Requirements
- **Node.js** 18.0.0 or higher
- **npm** 8.0.0 or higher (or **yarn** 1.22.0+)
- **Python** 3.8+ (for dictionary generation)
- **Git** for version control

### Development Tools (Recommended)
- **VSCode** with TypeScript and React extensions
- **Chrome DevTools** for debugging
- **React Developer Tools** browser extension

## Local Development Setup

### 1. Environment Setup
```bash
# Verify Node.js version
node --version  # Should be 18+

# Verify Python version
python --version  # Should be 3.8+

# Clone the repository
git clone <repository-url>
cd word-snake-game

# Install Node.js dependencies
npm install
```

### 2. Dictionary Generation (First Time Setup)
```bash
# Install Python dependencies for script
cd scripts
pip install -r requirements.txt

# Generate dictionary file
cd ..
npm run generate-dict

# Verify dictionary file was created
ls -la public/database.json
```

**Note**: The dictionary generation script downloads ~200,000 English words and filters them for the game. This process takes 1-2 minutes and creates a ~5MB database.json file.

### 3. Start Development Server
```bash
# Start the development server
npm run dev

# Open browser to http://localhost:5173
# The game should load with keyboard/touch controls
```

### 4. Development Workflow
```bash
# Run tests
npm run test

# Run tests in watch mode
npm run test:watch

# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure Explained

```
word-snake-game/
├── public/                    # Static assets
│   ├── database.json         # Generated dictionary (do not commit)
│   ├── index.html           # HTML entry point
│   └── favicon.ico          # Game icon
├── src/                      # Source code
│   ├── components/          # React components
│   ├── services/           # Business logic services
│   ├── hooks/              # Custom React hooks
│   ├── utils/              # Utility functions
│   ├── styles/             # Global styles
│   ├── types/              # TypeScript type definitions
│   └── App.tsx             # Main app component
├── scripts/                 # Build and setup scripts
│   ├── generate_dictionary.py
│   ├── requirements.txt
│   └── README.md
├── tests/                   # Test files
├── docs/                    # Documentation
└── package.json            # Project configuration
```

## Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Create optimized production build |
| `npm run preview` | Preview production build locally |
| `npm run test` | Run test suite |
| `npm run test:watch` | Run tests in watch mode |
| `npm run lint` | Check code for linting errors |
| `npm run type-check` | Validate TypeScript types |
| `npm run generate-dict` | Generate dictionary file from online sources |
| `npm run clean` | Clean build artifacts and node_modules |

## Game Controls

### Keyboard Controls
- **Arrow Keys** or **WASD**: Move snake
- **Space**: Pause/Resume game
- **R**: Restart game
- **ESC**: Return to main menu

### Touch Controls (Mobile)
- **Directional Buttons**: Displayed automatically on touch devices
- **Tap**: Pause/Resume (tap game area)

## Configuration

### Game Settings (`src/utils/constants.ts`)
```typescript
export const GAME_CONFIG = {
  GRID_SIZE: 20,              // Grid cell size in pixels
  SNAKE_SPEED: 150,           // Movement speed in milliseconds
  FOOD_SPAWN_INTERVAL: 5000,  // New letter every 5 seconds
  MAX_FOODS_ON_SCREEN: 20,    // Pause spawning at 20 letters
  MAX_SNAKE_LETTERS: 8,       // Death condition
  VOWEL_PROBABILITY: 0.33     // 1 in 3 letters will be vowels
};
```

### Development Configuration
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
});
```

## Testing

### Running Tests
```bash
# Run all tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm run test -- Snake.test.tsx

# Debug tests
npm run test:debug
```

### Test Structure
```
tests/
├── components/
│   ├── Snake.test.tsx
│   ├── GameBoard.test.tsx
│   └── ControlPanel.test.tsx
├── services/
│   ├── WordValidator.test.ts
│   └── GameEngine.test.ts
├── utils/
│   └── helpers.test.ts
└── __mocks__/
    └── database.json
```

## Deployment to Netlify

### Method 1: Git Integration (Recommended)

#### 1. Prepare Repository
```bash
# Ensure clean repository
git add .
git commit -m "Ready for deployment"
git push origin main

# Create .gitignore entry for generated files
echo "public/database.json" >> .gitignore
```

#### 2. Netlify Configuration
Create `netlify.toml` in project root:
```toml
[build]
  publish = "dist"
  command = "npm run build"

[build.environment]
  NODE_VERSION = "18"
  PYTHON_VERSION = "3.9"

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"

[[headers]]
  for = "*.js"
  [headers.values]
    Cache-Control = "public, max-age=31536000"

[[headers]]
  for = "*.css"
  [headers.values]
    Cache-Control = "public, max-age=31536000"

[[headers]]
  for = "/database.json"
  [headers.values]
    Cache-Control = "public, max-age=86400"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

#### 3. Deploy via Netlify Dashboard
1. Go to [netlify.com](https://netlify.com) and sign in
2. Click "New site from Git"
3. Connect your GitHub/GitLab repository
4. Configure build settings:
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`
   - **Node version**: `18`
5. Click "Deploy site"

#### 4. Environment Variables (if needed)
```bash
# In Netlify dashboard > Site settings > Environment variables
NODE_VERSION=18
PYTHON_VERSION=3.9
```

### Method 2: Manual Deployment

#### 1. Build Locally
```bash
# Generate dictionary and build
npm run generate-dict
npm run build

# Verify build output
ls -la dist/
```

#### 2. Deploy via Netlify CLI
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Deploy to production
netlify deploy --prod --dir=dist
```

### Method 3: Drag & Drop Deployment

#### 1. Create Production Build
```bash
# Complete build process
npm install
npm run generate-dict
npm run build

# Create deployment package
zip -r word-snake-deploy.zip dist/
```

#### 2. Manual Upload
1. Go to [netlify.com/drop](https://netlify.com/drop)
2. Drag the `dist` folder to the deployment area
3. Netlify will provide a temporary URL
4. Claim the site to make it permanent

## Deployment Troubleshooting

### Common Issues

#### 1. Dictionary File Missing
**Error**: `Failed to load /database.json`
**Solution**: 
```bash
# Ensure dictionary is generated before build
npm run generate-dict
npm run build
```

#### 2. Build Fails on Netlify
**Error**: `Python not found`
**Solution**: Add to `netlify.toml`:
```toml
[build.environment]
  PYTHON_VERSION = "3.9"
```

#### 3. TypeScript Errors
**Error**: `Type errors in build`
**Solution**:
```bash
# Fix type errors locally first
npm run type-check
# Fix reported errors, then redeploy
```

#### 4. Large Bundle Size
**Error**: `Bundle too large`
**Solution**: 
- Dictionary file should be in `public/` not bundled
- Check build output with `npm run build -- --analyze`

### Performance Optimization for Production

#### 1. Dictionary Optimization
```python
# In generate_dictionary.py, add compression
import gzip
import json

# After generating dictionary
with gzip.open('public/database.json.gz', 'wt') as f:
    json.dump(dictionary_data, f)
```

#### 2. Build Optimization
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          game: ['src/services/', 'src/utils/']
        }
      }
    }
  }
});
```

## Monitoring & Analytics

### Build Status
Monitor builds in Netlify dashboard:
- **Build time**: Should be < 3 minutes
- **Bundle size**: Target < 2MB total
- **Lighthouse score**: Target 90+ performance

### Performance Monitoring
```typescript
// Add to main App component
if (process.env.NODE_ENV === 'production') {
  // Web Vitals monitoring
  import('web-vitals').then(({ getLCP, getFID, getFCP, getCLS, getTTFB }) => {
    getLCP(console.log);
    getFID(console.log);
    getFCP(console.log);
    getCLS(console.log);
    getTTFB(console.log);
  });
}
```

## Support & Maintenance

### Updating Dictionary
```bash
# Regenerate dictionary with latest words
npm run generate-dict
git add public/database.json
git commit -m "Update dictionary"
git push origin main
# Netlify will auto-deploy
```

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement changes following SOLID principles
3. Add tests for new functionality
4. Update documentation if needed
5. Create pull request for review

### Debugging Production Issues
```bash
# Build and test locally first
npm run build
npm run preview

# Check browser console for errors
# Test on multiple devices/browsers
# Verify all game mechanics work correctly
```

## License & Credits

### Dictionary Sources
- Primary: [dwyl/english-words](https://github.com/dwyl/english-words)
- Fallback: SCOWL (Spell Checker Oriented Word Lists)

### Dependencies
- **React**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server
- **Tailwind CSS**: Utility-first styling
- **Jest**: Testing framework

---

For issues, feature requests, or contributions, please refer to the project's GitHub repository.