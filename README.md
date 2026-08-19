# <img src="webgame/favicon.svg" width="32" height="32" valign="middle" alt="Drone Safari logo" /> Wild Drone LLM Workshop

[![Version](https://img.shields.io/badge/version-1.3.0-8B5CF6?style=flat-square)](https://github.com/alejp1998/wilddrone-llm-workshop)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-57%20passed-10B981?style=flat-square)](tests/)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776AB?style=flat-square)](https://python.org)
[![Play](https://img.shields.io/badge/Play%20the%20Game-GitHub%20Pages-10B981?style=flat-square)](https://alejp1998.github.io/wilddrone-llm-workshop/)

Learn to build AI agents that understand natural language and control robotic systems through hands-on drone safari automation.

> 🎮 **Play the PixiJS web game right now** — no setup, runs in your browser:
> **[https://alejp1998.github.io/wilddrone-llm-workshop/](https://alejp1998.github.io/wilddrone-llm-workshop/)**
> (arrow keys to fly, Space to photograph, or use the on-screen controls)

![Drone Safari web game](docs/webgame_light.png)

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

### ☁️ Run in Google Colab (recommended for learners)

The `colab/` folder contains self-contained Colab versions of both notebooks —
they download the game scripts automatically and read your API key from Colab
secrets, so no local setup is needed:

| Notebook              | Open in Colab                                                                                                                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Part 1 — Travel Agent | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/alejp1998/wilddrone-llm-workshop/blob/main/colab/part1-travel-agent-colab.ipynb) |
| Part 2 — Drone Safari | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/alejp1998/wilddrone-llm-workshop/blob/main/colab/part2-drone-safari-colab.ipynb) |

1. Click **Open in Colab** for the part you want.
2. Add your API key as a Colab secret: click the 🔑 key icon → **Add new secret** → name it `GOOGLE_API_KEY` and paste your key.
3. **Runtime → Run all**.

### 💻 Run Locally

1. **Clone & Install**

   ```bash
   git clone https://github.com/alejp1998/wilddrone-llm-workshop.git
   cd wilddrone-llm-workshop
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **API Key**

   ```bash
   cp .env.example .env
   # Edit .env and add: GEMINI_API_KEY=your_key_here
   ```

   Get your key from: <https://aistudio.google.com/app/apikey>

   > 💡 The default model is `gemini/gemini-2.5-flash`. You can switch providers
   > without touching the notebooks by setting `LLM_MODEL` in your environment,
   > e.g. `LLM_MODEL=openai/gpt-4o-mini` or `LLM_MODEL=anthropic/claude-sonnet-4.5`
   > (requires the matching API key in `.env`).

3. **Start Learning**

   - Beginners: Open `part1-travel-agent.ipynb`
   - Experienced: Jump to `part2-drone-safari.ipynb`

### 🖼️ Screenshots

![Drone Safari](docs/webgame_light.png)

## 🎮 The Web Game (PixiJS)

A polished, browser-playable edition of the drone safari game lives in
[`webgame/`](webgame/) and is deployed to **GitHub Pages** — try it at
**[https://alejp1998.github.io/wilddrone-llm-workshop/](https://alejp1998.github.io/wilddrone-llm-workshop/)**.

- **PixiJS v8 renderer** with the workshop's pixel-art sprites (drone, zebra, elephant, oryx, trees)
- **Faithful logic port** — `webgame/js/game-core.js` mirrors `drone_safari_game.py`
  rule-for-rule (movement, crashes, scare mechanic, photo rules, win conditions, all 3 difficulties, sensors)
- **Cockpit UI** — system-aware dark/light theme, live HUD, safari album, on-screen D-pad, flight log, mission-failed/victory overlays
- **Keyboard**: `↑↓` move · `←→` turn · `Space`/`Enter` photo · `R` restart · `Q` quit

```bash
# Play locally
python3 -m http.server 8080 --directory webgame
# → http://localhost:8080
```

![Mission failed overlay](docs/webgame_failed.png)

The web game core ships with its own test suite (20 `node --test` cases verifying
parity with the Python engine) — run with `node --test webgame/tests/`.

## The Game

Navigate a drone in a 12x12 safari park to photograph 3 animal species (🦓🐘🦌) with only 5 pictures.

![Drone Safari game board](docs/screenshots/game_board.png)

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

- `part1-travel-agent.ipynb` - LLM fundamentals workshop (local edition)
- `part2-drone-safari.ipynb` - Drone command agent workshop (local edition)
- `colab/` - Self-contained Google Colab editions of both notebooks
- `webgame/` - PixiJS browser game (deployed to GitHub Pages)
- `llm_agents.py` - Agent utility classes (model overridable via `LLM_MODEL`)
- `drone_safari_game.py` - Complete game engine (pure numpy/matplotlib)
- `images/` - Game assets
- `tests/` - 37 unit tests for the game engine and agent utilities (no API key required)
- `webgame/tests/` - 20 node tests verifying web-game/engine parity

## Development

```bash
pip install -r requirements.txt
pytest                 # 37 tests: game rules, movement, photos, sensors, agent tooling
ruff check .           # lint
pre-commit install     # hooks: ruff, prettier, pytest
```

The test suite covers grid initialization and all difficulty maps, movement and
boundary/tree/animal crash rules, the "too close" scare mechanic, photo
consumption and win conditions, sensor summaries, and agent tool schema
generation and execution — all deterministic, no API keys needed.

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
