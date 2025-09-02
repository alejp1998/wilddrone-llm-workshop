# 🚁 Wild Drone LLM Workshop

An interactive workshop on Large Language Models (LLMs) and AI agents using drone safari game automation.

## Workshop Structure

### Part 1: LLM Fundamentals & Simple Tool-Calling Agent
- Understanding how LLMs work
- Tool calling and function execution
- Building a weather-based travel agent

### Part 2: Drone Safari Game Agent  
- Natural language command processing for game actions
- Single-agent game automation
- Tool integration (move, turn, take_picture)

### Part 3: Multi-Agent System (Advanced)
- Strategic planning vs execution agent separation
- Autonomous gameplay coordination
- Performance monitoring and analysis

## Files

- `wilddrone-llm-workshop.ipynb` - Main workshop notebook (educational focus)
- `llm_agents.py` - Agent implementations (complex code hidden here)
- `drone_safari_game.py` - The drone safari game engine
- `images/` - Game icons and graphics

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/alejp1998/wilddrone-ss-llm-workshop.git
cd wilddrone-ss-llm-workshop
```

### 2. Install Required Packages
```bash
pip install litellm matplotlib numpy python-dotenv
```

### 3. Set Up API Key
You need a Gemini API key to run the workshop. Get one from: https://aistudio.google.com/app/apikey

**Option A: Using .env file (Recommended)**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
GEMINI_API_KEY=your_actual_api_key_here
```

**Option B: Set environment variable**
```bash
export GEMINI_API_KEY=your_actual_api_key_here
```

**Option C: Set in notebook (not recommended for sharing)**
```python
import os
os.environ['GEMINI_API_KEY'] = 'your_actual_api_key_here'
```

### 4. Run the Workshop
Open `wilddrone-llm-workshop.ipynb` in Jupyter and follow along!

## 🔒 Security Note
Never commit your API keys to version control. The `.env` file is already in `.gitignore` to prevent this.

## Key Learning Focus

The workshop emphasizes **prompt engineering** and **agent design patterns** rather than implementation details. Students learn:

- How system prompts control agent behavior
- Tool calling mechanisms and protocols  
- Multi-agent coordination strategies
- Natural language interface design

Complex implementation details are hidden in `llm_agents.py` so students can focus on the conceptual understanding and prompt crafting.

#### Programmatic Mode (API)
```python
game = DroneSafariGame()
game.move('f')          # Move forward
game.turn('left')       # Turn left
game.take_picture()     # Take a picture
game.visualize()        # Show current state
```

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- matplotlib
- numpy

### Installation
```bash
git clone <repository-url>
cd wilddrone-ss-llm-workshop
pip install matplotlib numpy
```

### Running the Game
```bash
python3 drone_safari_game.py
```

## 📁 Project Structure

```
wilddrone-ss-llm-workshop/
├── drone_safari_game.py          # Main game implementation
├── images/                       # Game icons (optional)
│   ├── tree.png
│   ├── zebra.png
│   ├── elephant.png
│   ├── oryx.png
│   ├── drone.png
│   ├── crashed_drone.png
│   └── scared_animal.png
├── drone-safari-game.ipynb       # Jupyter notebook version
├── llm_robotics_workshop.ipynb   # Workshop materials
├── README.md
└── .gitignore
```

## 🎨 Game Features

### Visual Elements
- **Clean grid-based interface** with minimal cell boundaries
- **Icon-based graphics** with fallback colored squares
- **Real-time status display** showing pictures remaining, moves, turns
- **Dynamic titles** and color-coded feedback
- **Photo markers** showing where pictures were taken

### Game Mechanics
- **Relative movement system** based on drone's facing direction
- **Collision detection** for trees, animals, and boundaries
- **Distance-based photography** (exactly 2 cells away)
- **Animal behavior** (scared away if drone gets too close)
- **Performance tracking** (moves, turns, efficiency)

### Failure Conditions
- 🌳 **Tree Crash**: Flying into a tree
- 🚫 **Boundary Crash**: Flying outside the grid
- 🦓 **Animal Scared**: Getting too close to an animal (adjacent cell)
- 🐘 **Direct Collision**: Flying directly into an animal
- 📸 **Out of Pictures**: Using all 5 pictures without completing mission

## 🤖 LLM Integration

The game is designed for LLM robotics workshops and includes:

### Tool-Based Interface
Perfect for teaching LLMs to use tools:
- `move(direction)` - Navigate the drone
- `turn(direction)` - Change orientation  
- `take_picture()` - Capture wildlife photos
- `get_status()` - Get current game state

### Educational Use Cases
- **Tool Use Training**: Teach LLMs to interact with robotic systems
- **Spatial Reasoning**: Navigate 2D environments with obstacles
- **Planning and Strategy**: Optimize routes and picture-taking
- **Error Handling**: Recover from failures and learn from mistakes

## 🔧 Technical Details

### Core Classes
- **`DroneSafariGame`**: Main game logic and state management
- **`InteractiveDroneSafariGame`**: Keyboard-controlled interactive version

### Key Components
- **Grid Management**: 20x20 numpy array with entity tracking
- **Movement System**: Relative directions based on drone orientation
- **Visualization**: Matplotlib-based real-time graphics
- **State Tracking**: Comprehensive game statistics and history

### Configuration
```python
GRID_SIZE = 20          # Grid dimensions
EMPTY, TREE = 0, 1      # Cell type constants  
ZEBRA, ELEPHANT, ORYX = 2, 3, 4  # Animal types
```

## 📊 Game Statistics

The game tracks detailed statistics for performance analysis:
- **Total Moves**: Number of movement commands
- **Total Turns**: Number of rotation commands
- **Pictures Used**: Out of 5 maximum
- **Animals Photographed**: Progress tracking
- **Mission Efficiency**: Moves + turns per successful photo

## 🎓 Workshop Integration

### Jupyter Notebook Support
- Pre-built cells for game initialization
- Step-by-step tutorial progression
- Interactive visualization updates
- Code examples and exercises

### LLM Training Scenarios
1. **Basic Navigation**: Move around obstacles
2. **Systematic Search**: Find all animals efficiently  
3. **Strategic Planning**: Minimize moves while maximizing success
4. **Error Recovery**: Handle crashes and failed attempts
5. **Natural Language**: Convert human instructions to actions

## 🐛 Troubleshooting

### Common Issues
- **Icons not loading**: Game uses fallback colored squares
- **Keyboard not responding**: Click on the game window first
- **Game window not appearing**: Check matplotlib backend configuration

### Debug Mode
```python
game = DroneSafariGame()
game.print_instructions()  # Show detailed rules
status = game.get_status()  # Get current state
print(status)
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Happy Flying! 🚁📸**
