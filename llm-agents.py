"""
LLM Agents Implementation
This module contains the implementation details for the LLM workshop agents.
The complex code is hidden here so the notebook can focus on educational content.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import litellm

# Import the drone game
try:
    from drone_safari_game import DroneSafariGame
except ImportError:
    print("⚠️ Note: drone_safari_game.py needs to be in the same directory")


class SimpleAgent:
    """
    A simple LLM agent that can call tools
    """
    
    def __init__(self, model: str = "gemini/gemini-2.5-flash"):
        self.model = model
        self.tools = {}
        self.conversation_history = []
    
    def add_tool(self, name: str, function: callable, description: str):
        """Add a tool that the agent can use"""
        self.tools[name] = {
            "function": function,
            "description": description
        }
    
    def _get_tool_descriptions(self) -> str:
        """Get descriptions of available tools"""
        if not self.tools:
            return "No tools available."
        
        descriptions = "Available tools:\n"
        for name, tool in self.tools.items():
            descriptions += f"- {name}: {tool['description']}\n"
        return descriptions
    
    def _execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool with given parameters"""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found"
        
        try:
            return self.tools[tool_name]["function"](**kwargs)
        except Exception as e:
            return f"Error executing {tool_name}: {e}"
    
    def chat(self, user_message: str) -> str:
        """
        Process user message and potentially call tools
        """
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Create system prompt with tool information
        system_prompt = f"""
        You are a helpful AI assistant. You have access to tools that you can use to help answer questions.
        
        {self._get_tool_descriptions()}
        
        When you need to use a tool, respond with:
        TOOL_CALL: tool_name(parameter1=value1, parameter2=value2)
        
        For example:
        TOOL_CALL: get_weather_forecast(city="Paris", days=5)
        
        If you don't need tools, just respond normally.
        """
        
        # Prepare messages for LLM
        messages = [{"role": "system", "content": system_prompt}] + self.conversation_history
        
        try:
            # Get LLM response
            response = litellm.completion(
                model=self.model,
                messages=messages,
                max_tokens=300,
                temperature=0.1
            )
            
            llm_response = response.choices[0].message.content
            
            # Check if LLM wants to call a tool
            if "TOOL_CALL:" in llm_response:
                tool_call = llm_response.split("TOOL_CALL:")[1].strip()
                
                # Parse tool call (simple parsing for demo)
                if "(" in tool_call and ")" in tool_call:
                    tool_name = tool_call.split("(")[0].strip()
                    params_str = tool_call.split("(")[1].split(")")[0]
                    
                    # Parse parameters (very basic parsing)
                    params = {}
                    if params_str:
                        for param in params_str.split(","):
                            if "=" in param:
                                key, value = param.split("=", 1)
                                key = key.strip()
                                value = value.strip().strip('"\'')
                                # Try to convert to int if possible
                                try:
                                    value = int(value)
                                except:
                                    pass
                                params[key] = value
                    
                    # Execute tool
                    tool_result = self._execute_tool(tool_name, **params)
                    
                    # Get final response from LLM with tool result
                    tool_message = f"Tool result from {tool_name}: {json.dumps(tool_result, indent=2)}"
                    self.conversation_history.append({"role": "assistant", "content": tool_message})
                    
                    final_messages = messages + [{"role": "assistant", "content": tool_message}]
                    final_messages.append({"role": "user", "content": "Based on this tool result, provide a helpful response to my original question."})
                    
                    final_response = litellm.completion(
                        model=self.model,
                        messages=final_messages,
                        max_tokens=300,
                        temperature=0.1
                    )
                    
                    response_text = final_response.choices[0].message.content
                    
                else:
                    response_text = "Error: Could not parse tool call"
            else:
                response_text = llm_response
            
            # Add response to history
            self.conversation_history.append({"role": "assistant", "content": response_text})
            return response_text
            
        except Exception as e:
            return f"Error: {e}. Please check your model configuration."


class DroneAgent:
    """
    An LLM agent that can play the Drone Safari game using natural language commands
    """
    
    def __init__(self, game: DroneSafariGame, model: str = "gemini/gemini-2.5-flash"):
        self.game = game
        self.model = model
        self.action_history = []
    
    def _get_game_state_description(self) -> str:
        """Get a text description of the current game state"""
        status = self.game.get_status()
        
        description = f"""
Current Game State:
- Drone Position: Row {status['position'][0]}, Column {status['position'][1]}
- Facing Direction: {status['facing']}
- Pictures Remaining: {status['pictures_remaining']}/5
- Pictures Taken: {status['pictures_taken']}
- Total Moves: {status['total_moves']}
- Total Turns: {status['total_turns']}

Animals to Photograph:
"""
        
        for animal, photographed in status['animals_photographed'].items():
            status_emoji = "✅" if photographed else "❌"
            description += f"- {animal.capitalize()}: {status_emoji}\n"
        
        if status['photographed_locations']:
            description += f"\nPhotographed Locations: {list(status['photographed_locations'].keys())}"
        
        description += f"\nLast Action Result: {status['message']}"
        
        if status['game_over']:
            if status['game_won']:
                description += "\n🎉 GAME WON! All animals photographed!"
            else:
                description += f"\n💥 GAME OVER! Reason: {status.get('failure_reason', 'Unknown')}"
        
        return description
    
    def _parse_action_from_llm_response(self, response: str) -> tuple:
        """
        Parse the LLM response to extract the action to take
        Returns: (action_type, parameters)
        """
        response = response.lower().strip()
        
        # Look for explicit action calls
        if "move(" in response:
            # Extract direction from move() call
            start = response.find("move(") + 5
            end = response.find(")", start)
            direction = response[start:end].strip().strip("'\"")
            return ("move", direction)
        
        elif "turn(" in response:
            # Extract direction from turn() call  
            start = response.find("turn(") + 5
            end = response.find(")", start)
            direction = response[start:end].strip().strip("'\"")
            return ("turn", direction)
        
        elif "take_picture()" in response or "take picture" in response:
            return ("take_picture", None)
        
        # Fallback to keyword detection
        elif "forward" in response or "ahead" in response:
            return ("move", "f")
        elif "backward" in response or "back" in response:
            return ("move", "b")
        elif "left" in response and "turn" in response:
            return ("turn", "left")
        elif "right" in response and "turn" in response:
            return ("turn", "right")
        elif "left" in response:
            return ("move", "l")
        elif "right" in response:
            return ("move", "r")
        elif "picture" in response or "photo" in response:
            return ("take_picture", None)
        
        return ("unknown", None)
    
    def get_system_prompt(self):
        """Return the system prompt used by the drone agent"""
        return """
You are an AI agent controlling a drone in a safari photography game. Your goal is to photograph all animals (zebra, elephant, oryx) without crashing.

RULES:
1. Stay 2 cells away from animals when taking pictures
2. Don't crash into trees or fly outside the grid
3. Don't get too close to animals (adjacent cells) - they'll get scared!
4. You have limited pictures (5 total)

AVAILABLE ACTIONS:
- move('f') - move forward
- move('b') - move backward  
- move('l') - move left
- move('r') - move right
- turn('left') - turn left
- turn('right') - turn right
- take_picture() - take a photograph

Based on the user's command and current game state, respond with the exact action to take.
For example: "move('f')" or "turn('right')" or "take_picture()"

Always include your reasoning and the specific action call.
"""
    
    def process_command(self, natural_language_command: str) -> str:
        """
        Process a natural language command and execute the appropriate game action
        """
        if self.game.game_over:
            return "Game is over! Please reset the game to continue."
        
        # Get current game state
        game_state = self._get_game_state_description()
        
        # Create prompt for the LLM
        system_prompt = self.get_system_prompt()
        
        user_prompt = f"""
Current game state:
{game_state}

User command: "{natural_language_command}"

What action should I take? Respond with your reasoning and the exact action call.
"""
        
        try:
            # Get LLM response
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            llm_response = response.choices[0].message.content
            
            # Parse and execute action
            action_type, parameter = self._parse_action_from_llm_response(llm_response)
            
            if action_type == "move":
                result = self.game.move(parameter)
                self.action_history.append(f"move({parameter}) -> {result}")
            elif action_type == "turn":
                result = self.game.turn(parameter)
                self.action_history.append(f"turn({parameter}) -> {result}")
            elif action_type == "take_picture":
                result = self.game.take_picture()
                self.action_history.append(f"take_picture() -> {result}")
            else:
                result = f"Could not understand action from: {llm_response}"
            
            return f"LLM Reasoning: {llm_response}\n\nAction Result: {result}"
            
        except Exception as e:
            return f"Error processing command: {e}"
    
    def get_action_history(self) -> List[str]:
        """Get the history of actions taken"""
        return self.action_history.copy()


class StrategicPlanningAgent:
    """
    A strategic planning agent that analyzes the game state and makes high-level decisions
    """
    
    def __init__(self, model: str = "gemini/gemini-2.5-flash"):
        self.model = model
        self.decision_history = []
        self.current_target = None
        self.exploration_phase = True
    
    def _analyze_game_state(self, game: DroneSafariGame) -> str:
        """Analyze the current game state and create a detailed description"""
        status = game.get_status()
        
        # Get grid information by inspecting the game grid
        analysis = f"""
GAME STATE ANALYSIS:
==================

Current Status:
- Drone Position: Row {status['position'][0]}, Column {status['position'][1]}
- Facing Direction: {status['facing']} 
- Pictures Remaining: {status['pictures_remaining']}/5
- Pictures Taken: {status['pictures_taken']}

Mission Progress:
"""
        
        # Analyze animal photography status
        animals_left = []
        animals_done = []
        
        for animal, photographed in status['animals_photographed'].items():
            if photographed:
                animals_done.append(animal)
            else:
                animals_left.append(animal)
        
        analysis += f"- Completed: {animals_done}\n"
        analysis += f"- Remaining: {animals_left}\n"
        
        # Animal locations (from the game setup)
        animal_locations = {
            "zebra": (5, 5),
            "elephant": (15, 15),
            "oryx": (3, 15)
        }
        
        analysis += "\nKnown Animal Locations:\n"
        for animal, location in animal_locations.items():
            status_symbol = "✅" if animal in animals_done else "🎯"
            analysis += f"- {animal.capitalize()}: Row {location[0]}, Column {location[1]} {status_symbol}\n"
        
        # Calculate distances to each remaining animal
        if animals_left:
            analysis += "\nDistances to Remaining Animals:\n"
            for animal in animals_left:
                location = animal_locations[animal]
                distance = abs(status['position'][0] - location[0]) + abs(status['position'][1] - location[1])
                analysis += f"- {animal.capitalize()}: {distance} moves away\n"
        
        # Safety considerations
        analysis += f"\nSafety Status:\n"
        analysis += f"- Current position should be safe from animals\n"
        analysis += f"- Must maintain 2-cell distance when photographing\n"
        analysis += f"- Watch out for trees and grid boundaries\n"
        
        # Photo efficiency
        if status['pictures_taken'] > 0:
            efficiency = len(animals_done) / status['pictures_taken'] * 100
            analysis += f"\nPhoto Efficiency: {efficiency:.1f}% (successful photos/total taken)\n"
        
        return analysis
    
    def get_system_prompt(self):
        """Return the system prompt used by the strategic planning agent"""
        return """
You are a strategic planning agent for a drone safari photography mission. Your job is to analyze the game state and provide clear natural language commands to a drone control agent.

MISSION OBJECTIVE: Photograph all three animals (zebra, elephant, oryx) efficiently with only 5 pictures.

STRATEGIC CONSIDERATIONS:
1. Plan the most efficient route to visit all animals
2. Approach animals from exactly 2 cells away for photography
3. Avoid wasting pictures on empty spaces or trees
4. Navigate safely around obstacles
5. Consider the drone's current facing direction for efficient movement

RESPONSE FORMAT:
Provide a clear, specific natural language command that the drone control agent can execute.

Examples of good commands:
- "Move forward towards the zebra at position (5,5)"
- "Turn left to face the elephant"
- "Move closer to get within photo range of the oryx" 
- "Take a picture of the animal ahead"
- "Navigate east to avoid the tree"

Be specific and actionable!
"""
    
    def decide_next_action(self, game: DroneSafariGame) -> str:
        """
        Analyze the game state and decide what to do next
        Returns a natural language command for the drone control agent
        """
        
        if game.game_over:
            return "Game is over - no action needed"
        
        # Get detailed game analysis
        game_analysis = self._analyze_game_state(game)
        
        # Create decision prompt
        system_prompt = self.get_system_prompt()
        
        user_prompt = f"""
Current game analysis:
{game_analysis}

Based on this analysis, what should the drone do next? Provide a clear natural language command.
Consider the most efficient strategy to complete the mission.
"""
        
        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.2
            )
            
            decision = response.choices[0].message.content.strip()
            
            # Log the decision
            status = game.get_status()
            self.decision_history.append({
                "turn": len(self.decision_history) + 1,
                "position": status['position'].copy(),
                "facing": status['facing'],
                "decision": decision,
                "animals_left": [animal for animal, done in status['animals_photographed'].items() if not done],
                "pictures_remaining": status['pictures_remaining']
            })
            
            return decision
            
        except Exception as e:
            return f"Error in strategic planning: {e}"
    
    def get_decision_history(self) -> List[Dict]:
        """Get the history of strategic decisions"""
        return self.decision_history.copy()


class MultiAgentSystem:
    """
    Coordinates multiple agents to play the drone safari game autonomously
    """
    
    def __init__(self, game: DroneSafariGame, model: str = "gemini/gemini-2.5-flash"):
        self.game = game
        self.strategic_agent = StrategicPlanningAgent(model)
        self.drone_agent = DroneAgent(game, model)
        self.step_count = 0
        self.max_steps = 50  # Safety limit to prevent infinite loops
        
    def run_autonomous_game(self, show_steps: bool = True, max_steps: Optional[int] = None) -> Dict[str, Any]:
        """
        Run the game autonomously using the multi-agent system
        """
        if max_steps:
            self.max_steps = max_steps
            
        print("🚀 Starting Autonomous Multi-Agent Game!")
        print("="*60)
        
        step_log = []
        
        while not self.game.game_over and self.step_count < self.max_steps:
            self.step_count += 1
            
            if show_steps:
                print(f"\n🔄 STEP {self.step_count}")
                print("-" * 30)
            
            # Strategic agent decides what to do
            strategic_decision = self.strategic_agent.decide_next_action(self.game)
            
            if show_steps:
                print(f"🧠 Strategic Agent: {strategic_decision}")
            
            # Drone agent executes the decision
            execution_result = self.drone_agent.process_command(strategic_decision)
            
            if show_steps:
                print(f"🚁 Drone Agent: {execution_result}")
                
                # Show current status
                status = self.game.get_status()
                print(f"📍 Position: {status['position']}, Facing: {status['facing']}")
                print(f"📸 Pictures: {status['pictures_remaining']}/{5}")
                
                animals_status = []
                for animal, done in status['animals_photographed'].items():
                    emoji = "✅" if done else "❌" 
                    animals_status.append(f"{animal}{emoji}")
                print(f"🎯 Animals: {' '.join(animals_status)}")
            
            # Log this step
            step_log.append({
                "step": self.step_count,
                "strategic_decision": strategic_decision,
                "execution_result": execution_result,
                "game_state": self.game.get_status().copy()
            })
            
            # Small delay for readability
            if show_steps:
                import time
                time.sleep(0.5)
        
        # Game finished - show results
        final_status = self.game.get_status()
        
        print("\n" + "="*60)
        print("🏁 GAME FINISHED!")
        print("="*60)
        
        if final_status['game_won']:
            print("🎉 SUCCESS! All animals photographed!")
            print(f"✨ Completed in {self.step_count} steps")
            print(f"📸 Used {final_status['pictures_taken']}/5 pictures")
            print(f"🚁 Total moves: {final_status['total_moves']}")
            print(f"🔄 Total turns: {final_status['total_turns']}")
        else:
            print("💥 Mission Failed!")
            print(f"🛑 Reason: {final_status.get('failure_reason', 'Unknown')}")
            print(f"⏱️  Steps taken: {self.step_count}")
            print(f"📸 Pictures used: {final_status['pictures_taken']}/5")
        
        # Show final visualization
        self.game.visualize()
        
        return {
            "success": final_status['game_won'],
            "steps_taken": self.step_count,
            "pictures_used": final_status['pictures_taken'],
            "total_moves": final_status['total_moves'],
            "total_turns": final_status['total_turns'],
            "animals_photographed": final_status['animals_photographed'],
            "step_log": step_log,
            "failure_reason": final_status.get('failure_reason')
        }
    
    def get_performance_summary(self) -> str:
        """Get a summary of the multi-agent system performance"""
        strategic_history = self.strategic_agent.get_decision_history()
        drone_history = self.drone_agent.get_action_history()
        
        summary = f"""
MULTI-AGENT PERFORMANCE SUMMARY:
===============================

Strategic Decisions Made: {len(strategic_history)}
Drone Actions Executed: {len(drone_history)}
Total Game Steps: {self.step_count}

Strategic Decision Pattern:
"""
        
        for i, decision in enumerate(strategic_history[-5:], 1):  # Show last 5 decisions
            summary += f"{i}. {decision['decision']}\n"
        
        return summary


# Tool functions for the weather agent
def get_weather_forecast(city: str, days: int = 7) -> Dict[str, Any]:
    """
    Get weather forecast for a city (mock implementation)
    In a real scenario, you'd use a weather API like OpenWeatherMap
    """
    # Mock weather data for demonstration
    import random
    
    weather_conditions = ["sunny", "partly cloudy", "cloudy", "rainy", "stormy"]
    
    forecast = {
        "city": city,
        "days": days,
        "forecast": []
    }
    
    for i in range(days):
        day_forecast = {
            "day": i + 1,
            "condition": random.choice(weather_conditions),
            "temperature": random.randint(15, 30),
            "humidity": random.randint(40, 80),
            "wind_speed": random.randint(5, 25)
        }
        forecast["forecast"].append(day_forecast)
    
    return forecast


def get_travel_info(destination: str) -> Dict[str, Any]:
    """
    Get basic travel information about a destination (mock implementation)
    """
    # Mock travel data
    travel_info = {
        "Paris": {
            "country": "France",
            "best_season": "Spring/Summer",
            "attractions": ["Eiffel Tower", "Louvre Museum", "Notre-Dame"],
            "average_cost_per_day": "$150-200"
        },
        "Tokyo": {
            "country": "Japan", 
            "best_season": "Spring/Fall",
            "attractions": ["Senso-ji Temple", "Tokyo Tower", "Shibuya Crossing"],
            "average_cost_per_day": "$120-180"
        },
        "Barcelona": {
            "country": "Spain",
            "best_season": "Spring/Summer", 
            "attractions": ["Sagrada Familia", "Park Güell", "Las Ramblas"],
            "average_cost_per_day": "$100-150"
        }
    }
    
    return travel_info.get(destination, {
        "country": "Unknown",
        "best_season": "Year-round",
        "attractions": ["Local sights"],
        "average_cost_per_day": "$100-200"
    })
