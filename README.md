# 🚁 Wild Drone LLM Workshop

An interactive workshop on Large Language Models (LLMs) and AI agents using drone safari game automation. Learn how to build AI agents that can understand natural language and control robotic systems through hands-on exercises.

## Workshop Structure

### Part 1: LLM Fundamentals & Tool-Calling Agent (`part1-travel-agent.ipynb`)
- **Understanding LLMs**: How large language models process and generate text
- **Tool Integration**: Teaching LLMs to use external functions and APIs
- **Building a Travel Agent**: Create an AI that can check weather and recommend destinations
- **Prompt Engineering**: Learn how system prompts control agent behavior

### Part 2: Drone Safari Game Agent (`part2-drone-safari.ipynb`)
- **Natural Language Commands**: Transform human speech into precise game actions
- **Game Automation**: Build agents that can navigate and photograph wildlife
- **Progressive Complexity**: From single commands to multi-step instruction sequences
- **Interactive Testing**: Use built-in Jupyter widgets to test your agents in real-time

## Repository Files

### Core Workshop Materials
- `part1-travel-agent.ipynb` - Travel agent workshop with tool-calling fundamentals
- `part2-drone-safari.ipynb` - Drone command agent with game integration
- `llm_agents.py` - Reusable agent classes and utility functions
- `drone_safari_game.py` - Complete drone safari game engine with visualization

### Supporting Files
- `images/` - Game assets (drone, animals, terrain icons)
- `.env.example` - Template for API key configuration
- `LICENSE` - MIT license
- `README.md` - This documentation


### 1. Clone the Repository

```bash
git clone https://github.com/alejp1998/wilddrone-ss-llm-workshop.git
cd wilddrone-ss-llm-workshop
```

### 2. Install Required Packages

```bash
pip install litellm matplotlib numpy python-dotenv ipywidgets
```

*Note: For OpenAI instead of Gemini, also install: `pip install openai`*

### 3. Set Up API Key

You need a Gemini API key to run the workshop. Get one from: <https://aistudio.google.com/app/apikey>

#### Option A: Using .env file (Recommended)

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
GEMINI_API_KEY=your_actual_api_key_here
```

#### Option B: Set environment variable

```bash
export GEMINI_API_KEY=your_actual_api_key_here
```

#### Option C: Set in notebook (not recommended for sharing)

```python
import os
os.environ['GEMINI_API_KEY'] = 'your_actual_api_key_here'
```

### 4. Run the Workshop

Open either notebook in Jupyter and follow along:

- **Beginners**: Start with `part1-travel-agent.ipynb`
- **Experienced**: Jump to `part2-drone-safari.ipynb`

## 🔒 Security Note

Never commit your API keys to version control. The `.env` file is already in `.gitignore` to prevent this.

## 🎮 The Drone Safari Game

### Game Objective

Control a drone in a 12x12 grid safari park to photograph all three animal species:

- **🦓 Zebra** - Roams the grasslands
- **🐘 Elephant** - Wanders the open areas  
- **🦌 Oryx** - Grazes throughout the park

### Game Rules

- **📷 Limited Photos**: You have exactly 5 pictures to capture all 3 species
- **🌳 Obstacle Avoidance**: Trees will crash your drone - navigate carefully!
- **📏 Photo Distance**: Animals must be exactly 2 cells away for a good shot
- **😱 Animal Behavior**: Get too close (adjacent) and animals will flee!
- **🧭 Directional Movement**: Drone moves relative to its current facing direction

### Game Controls

#### Programmatic Interface (For AI Agents)

```python
from drone_safari_game import DroneSafariGame

game = DroneSafariGame()
game.move('f')          # Move forward
game.move('b')          # Move backward  
game.move('l')          # Move left
game.move('r')          # Move right
game.turn('left')       # Turn left
game.turn('right')      # Turn right
game.take_picture()     # Take a picture
game.visualize()        # Show current state
status = game.get_status()  # Get game information
```

#### Interactive Mode (For Human Players)

```bash
python3 drone_safari_game.py
```

Use WASD keys for movement, Q/E for turning, SPACE for photos.

## 🤖 Key Learning Objectives

### Prompt Engineering Fundamentals

- **System Prompts**: How to give AI agents personality and behavior guidelines
- **Tool Descriptions**: Writing clear function documentation for LLM understanding
- **Constraint Setting**: Teaching agents what they can and cannot do
- **Response Formatting**: Controlling how agents communicate back to users

### Tool-Calling Patterns

- **Function Registration**: How to expose Python functions to LLMs
- **Parameter Schemas**: Defining input validation and type safety
- **Error Handling**: Managing failures in tool execution
- **State Management**: Maintaining context across multiple tool calls

### Agent Design Principles

- **Single Responsibility**: Each agent should have one clear purpose
- **Separation of Concerns**: Strategy vs. execution separation
- **Natural Language Interface**: Converting human speech to precise actions
- **Progressive Complexity**: Building from simple to advanced behaviors

## 📋 Workshop Progression

### Part 1: Foundation Building

1. **LLM Basics** - Understand how language models work
2. **Simple Tools** - Create weather checking functions
3. **First Agent** - Build a travel recommendation system
4. **Testing & Refinement** - Learn debugging techniques

### Part 2: Game Integration

1. **Game Exploration** - Understand the drone safari environment
2. **Tool Creation** - Build movement, turning, and photography tools
3. **Command Agent** - Translate natural language to game actions
4. **Multi-Action Agent** - Handle complex multi-step commands
5. **Interactive Testing** - Use Jupyter widgets for real-time feedback

## 🔧 Technical Architecture

### Core Components

- **`LLMAgent`**: Base class for all AI agents with tool-calling capabilities
- **`TravelAgent`**: Specialized agent for travel planning (Part 1)
- **`DroneSafariGame`**: Complete game engine with visualization
- **`InteractiveNotebookAgent`**: Jupyter widget interface for testing

### LLM Integration

- **Provider Agnostic**: Uses `litellm` for multiple LLM providers (Gemini, OpenAI, etc.)
- **Tool Calling**: JSON-based function calling with parameter validation
- **Memory Management**: Conversation history and context preservation
- **Debug Support**: Enhanced logging and error reporting

## 🎨 Visualization Features

### Game Graphics

- **Icon-Based Rendering**: Custom PNG assets for all game elements
- **Fallback Support**: Colored squares if icons fail to load
- **Real-Time Updates**: Dynamic visualization after each action
- **Status Display**: Position, direction, photos remaining, mission progress

### Educational Displays

- **Agent Reasoning**: See LLM thought processes in real-time
- **Tool Execution**: Observe function calls and results
- **Error Feedback**: Clear error messages and troubleshooting hints
- **Progress Tracking**: Visual indicators of learning objectives

## 🏆 Success Metrics

### Game Performance

- **Mission Completion**: Successfully photograph all three animal species
- **Efficiency**: Minimize total moves and turns
- **Survival**: Avoid crashes and animal scares
- **Photo Management**: Optimize use of limited pictures

### Learning Outcomes

- **Prompt Quality**: Write effective system prompts and tool descriptions
- **Agent Behavior**: Create agents that follow instructions accurately
- **Natural Language**: Handle diverse ways of expressing the same intent
- **Debugging Skills**: Identify and fix agent misbehavior

## 🚀 Getting Started Tips

### For Beginners

1. **Start with Part 1** - Build foundational understanding
2. **Read the prompts** - Study provided examples carefully
3. **Experiment freely** - Try different phrasings and approaches
4. **Use debug mode** - Enable detailed logging to see agent reasoning

### For Advanced Users

1. **Jump to Part 2** - Focus on game integration challenges
2. **Modify the game** - Try changing rules or adding features
3. **Build new agents** - Create autonomous or strategic planning agents
4. **Optimize performance** - Challenge yourself with efficiency goals

## 📁 Directory Structure

```
wilddrone-ss-llm-workshop/
├── part1-travel-agent.ipynb      # LLM fundamentals & tool-calling
├── part2-drone-safari.ipynb      # Drone command agent workshop
├── llm_agents.py                 # Agent classes and utilities
├── drone_safari_game.py          # Complete game engine
├── images/                       # Game assets
│   ├── drone.png
│   ├── crashed_drone.png
│   ├── zebra.png
│   ├── elephant.png
│   ├── oryx.png
│   ├── tree.png
│   └── scared_animal.png
├── .env.example                  # API key template
├── .gitignore                    # Git ignore file
├── LICENSE                       # MIT license
└── README.md                     # This documentation
```

## 💡 Troubleshooting

### Common Issues

#### Icons not loading

- Game uses fallback colored squares if PNG files are missing
- Ensure `images/` directory contains all required assets

#### API key errors

- Verify your `.env` file has the correct format
- Check that your Gemini API key is valid and active
- Try setting the environment variable directly in terminal

#### Jupyter widgets not working

- Install widgets: `pip install ipywidgets`
- Enable extension: `jupyter nbextension enable --py widgetsnbextension`
- Restart Jupyter after installation

#### Import errors

- Ensure all files are in the same directory
- Verify required packages are installed
- Check Python version compatibility (3.7+)

### Debug Mode

```python
# Enable detailed logging for agents
agent.chat_with_debug(command, debug=True)

# Get detailed game status
game.get_status()

# Print game instructions
game.print_instructions()
```

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Additional game scenarios and challenges
- More sophisticated agent architectures  
- Extended tool libraries
- Educational content enhancements
- Bug fixes and performance improvements

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Happy Flying! 🚁📸

Built with ❤️ for AI education and robotics learning
