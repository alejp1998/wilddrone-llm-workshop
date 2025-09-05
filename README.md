# 🚁 Wild Drone LLM Workshop

Learn to build AI agents that understand natural language and control robotic systems through hands-on drone safari automation.

## Workshop Structure

**Part 1: LLM Fundamentals** (`part1-travel-agent.ipynb`)
- How LLMs work and process text
- Tool calling and function execution
- Building a weather-informed travel agent

**Part 2: Drone Safari Agent** (`part2-drone-safari.ipynb`)
- Natural language to game command translation
- Interactive agent testing with Jupyter widgets
- Progressive complexity from single to multi-step commands

## Quick Setup

1. **Clone & Install**

   ```bash
   git clone https://github.com/alejp1998/wilddrone-ss-llm-workshop.git
   cd wilddrone-ss-llm-workshop
   pip install litellm matplotlib numpy python-dotenv ipywidgets
   ```

2. **API Key**

   ```bash
   cp .env.example .env
   # Edit .env and add: GEMINI_API_KEY=your_key_here
   ```

   Get your key from: <https://aistudio.google.com/app/apikey>

3. **Start Learning**

   - Beginners: Open `part1-travel-agent.ipynb`
   - Experienced: Jump to `part2-drone-safari.ipynb`

## The Game

Navigate a drone in a 12x12 safari park to photograph 3 animal species (🦓🐘🦌) with only 5 pictures.

**Rules:**

- Avoid trees (🌳) and boundaries 
- Animals must be exactly 2 cells away for photos
- Too close = animals flee!

**API Controls (for agents):**

```python
game.move('forward')    # front/back/left/right  
game.turn('left')     # left/right
game.take_picture()   # capture photo
```

**Human Controls:**

- Arrow keys: Move drone
- A/D keys: Turn left/right  
- Enter: Take picture
- R: Restart, Q: Quit

## Files

- `part1-travel-agent.ipynb` - LLM fundamentals workshop
- `part2-drone-safari.ipynb` - Drone command agent workshop  
- `llm_agents.py` - Agent utility classes
- `drone_safari_game.py` - Complete game engine
- `images/` - Game assets

## Key Learning

- **Prompt Engineering**: Write system prompts that control agent behavior
- **Tool Integration**: Give LLMs access to external functions
- **Natural Language**: Handle diverse ways of expressing commands
- **Agent Design**: Single-purpose vs. multi-action agents

## Troubleshooting

**Missing widgets:** `pip install ipywidgets`  
**API errors:** Check your `.env` file format  
**Import errors:** Ensure all files are in the same directory

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Happy Flying! 🚁📸

Built with ❤️ for AI education and robotics learning
