"""
LLM Agents Implementation
This module contains agent implementations for the LLM workshop.
The tools and prompts are defined in the notebook for educational purposes.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import litellm
import json
import random
import copy

# Import the drone game
try:
    from drone_safari_game import DroneSafariGame
except ImportError:
    print("Note: drone_safari_game.py needs to be in the same directory")

# Function parameters metadata decorator for tool schemas
def add_parameters_schema(**schema):
    """Decorator to add parameter schema to functions for LLM tool calling"""
    def decorator(func):
        func.parameters_schema = schema
        return func
    return decorator


class TravelAgent:
    """
    An LLM agent that helps with travel planning using external tools and prompts
    Tools and system prompt are defined externally (in notebook) for educational purposes
    """
    
    def __init__(self, model: str = "gemini/gemini-1.5-flash", tools: List = None, system_prompt: str = None):
        self.model = model
        self.tools = tools or []
        self.system_prompt = system_prompt or "You are a helpful travel assistant."
        self.conversation_history = []
    
    def add_tool(self, tool_function):
        """Add a tool function to the agent"""
        self.tools.append(tool_function)
        print(f"Added tool: {tool_function.__name__}")
    
    def set_system_prompt(self, prompt: str):
        """Set the system prompt for the agent"""
        self.system_prompt = prompt
        print("System prompt updated!")

    def get_system_prompt(self):
        """Get the current system prompt"""
        return self.system_prompt

    def _get_tool_schemas(self):
        """Convert tool functions to OpenAI function calling format"""
        if not self.tools:
            return None
        
        schemas = []
        for tool in self.tools:
            if hasattr(tool, 'parameters_schema'):
                schema = {
                    "type": "function",
                    "function": {
                        "name": tool.__name__,
                        "description": tool.__doc__ or f"Execute {tool.__name__}",
                        "parameters": {
                            "type": "object",
                            "properties": tool.parameters_schema,
                            "required": [name for name, config in tool.parameters_schema.items() 
                                       if "default" not in config]
                        }
                    }
                }
                schemas.append(schema)
        return schemas

    def _execute_tool(self, tool_name: str, **kwargs):
        """Execute a tool by name with given arguments"""
        for tool in self.tools:
            if tool.__name__ == tool_name:
                try:
                    return tool(**kwargs)
                except Exception as e:
                    return f"Error executing {tool_name}: {e}"
        return f"Error: Tool '{tool_name}' not found"

    def chat(self, user_message: str, debug: bool = True, clear_memory: bool = True) -> str:
        """
        Process user message and potentially call tools
        
        Args:
            user_message: The message from the user
            debug: Whether to show debug information
            clear_memory: Whether to clear conversation history before processing (default: False)
        """
        if debug:
            print(f"- User Question: {user_message}")
            print(f"- Available tools: {[tool.__name__ for tool in self.tools]}")
        
        # Clear conversation history if requested
        if clear_memory:
            self.conversation_history = []
            if debug:
                print("- Conversation memory cleared")
        
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Prepare messages for LLM
        messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
        
        try:
            # Get tool schemas
            tool_schemas = self._get_tool_schemas()
            
            # Get LLM response
            response = litellm.completion(
                model=self.model,
                messages=messages,
                max_tokens=4000,
                temperature=0.1,
                tools=tool_schemas if tool_schemas else None
            )
            
            message = response.choices[0].message
            response_text = message.content or ""
            
            # Handle tool calls if present
            if hasattr(message, 'tool_calls') and message.tool_calls:
                if debug:
                    print(f"- Tools called: {[tc.function.name for tc in message.tool_calls]}")
                
                # Add the assistant's message with tool calls to history
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": response_text,
                    "tool_calls": [{"id": tc.id, "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in message.tool_calls]
                })
                
                # Execute tools and add results to conversation
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if debug:
                        print(f"- Executing {function_name} with args: {function_args}")
                    
                    # Execute the tool
                    tool_result = self._execute_tool(function_name, **function_args)
                    
                    if debug:
                        print(f"- Tool result: {tool_result}")
                    
                    # Add tool result to conversation history
                    self.conversation_history.append({
                        "role": "tool",
                        "content": str(tool_result),
                        "tool_call_id": tool_call.id
                    })
                
                # Get final response from LLM using tool results
                final_response = litellm.completion(
                    model=self.model,
                    messages=[{"role": "system", "content": self.system_prompt}] + self.conversation_history,
                    max_tokens=4000,
                    temperature=0.1
                )
                
                final_response_text = final_response.choices[0].message.content
                
                if debug:
                    print(f"- Final Answer: {final_response_text}")
                
                # Add final response to history
                self.conversation_history.append({"role": "assistant", "content": final_response_text})
                return final_response_text
            else:
                # No tool calls, return original response
                if debug:
                    print(f"- Final Answer (no tools used): {response_text}")
                
                self.conversation_history.append({"role": "assistant", "content": response_text})
                return response_text
            
        except Exception as e:
            return f"Error: {e}. Please check your model configuration."

# Drone Game Tools
@add_parameters_schema(
    direction={"type": "string", "enum": ["forward", "f", "left", "l", "right", "r", "back", "b"], 
               "description": "Direction to move: forward/f, left/l, right/r, back/b"}
)
def move_drone(direction: str) -> str:
    """Move the drone in the specified direction"""
    # This will be connected to the actual game instance in the DroneAgent
    return f"move_drone called with direction: {direction}"

@add_parameters_schema(
    direction={"type": "string", "enum": ["left", "right"], 
               "description": "Direction to turn: left or right"}
)
def turn_drone(direction: str) -> str:
    """Turn the drone left or right"""
    # This will be connected to the actual game instance in the DroneAgent
    return f"turn_drone called with direction: {direction}"

@add_parameters_schema()
def take_picture_drone() -> str:
    """Take a picture with the drone camera"""
    # This will be connected to the actual game instance in the DroneAgent
    return "take_picture_drone called"


class DroneAgent:
    """
    An LLM agent that can play the Drone Safari game using natural language commands
    """
    
    def __init__(self, game: DroneSafariGame, model: str = "gemini/gemini-1.5-flash"):
        self.game = game
        self.model = model
        self.action_history = []
        self.tools = []
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup the tools available to the drone agent"""
        self.tools = [move_drone, turn_drone, take_picture_drone]
    
    def get_system_prompt(self):
        """System prompt that defines the drone agent's behavior"""
        return """You are an AI drone pilot controlling a drone in a safari photography game.

Your mission: Photograph all three animals (zebra, elephant, oryx) without crashing.

GAME RULES:
- Don't crash into trees (T) or go outside the grid boundaries
- Don't get too close to animals or they'll get scared and run away
- Take pictures from exactly 2 cells away in the direction you're facing
- You have only 5 pictures total - use them wisely!

CURRENT SYMBOLS:
- D: Your drone position
- Z: Zebra, E: Elephant, O: Oryx (animals to photograph)
- T: Trees (obstacles - avoid these!)
- ~: Scared animals (can't photograph them anymore)

AVAILABLE ACTIONS:
- move_drone(direction): Move in direction ('forward'/'f', 'left'/'l', 'right'/'r', 'back'/'b')
- turn_drone(direction): Turn 'left' or 'right'
- take_picture_drone(): Take a photograph (only works if animal is 2 cells away in facing direction)

STRATEGY:
1. Analyze the current position and facing direction
2. Plan a safe route to an animal
3. Position yourself exactly 2 cells away from the animal
4. Face the animal and take a picture
5. Repeat for all animals

Always include your reasoning for the chosen action.
"""
    
    def _get_game_state_description(self) -> str:
        """Get a text description of the current game state"""
        status = self.game.get_status()
        
        description = f"""Current Game State:
- Drone Position: {status['position']}
- Facing Direction: {status['facing']}
- Pictures Remaining: {status['pictures_remaining']}/5
- Animals Photographed: {status['animals_photographed']}
- Game Over: {status['game_over']}

Grid Layout:
{self.game.get_grid_string()}
"""
        return description
    
    def _get_tool_schemas(self):
        """Convert tool functions to OpenAI function calling format"""
        if not self.tools:
            return None
        
        schemas = []
        for tool in self.tools:
            if hasattr(tool, 'parameters_schema'):
                schema = {
                    "type": "function",
                    "function": {
                        "name": tool.__name__,
                        "description": tool.__doc__ or f"Execute {tool.__name__}",
                        "parameters": {
                            "type": "object",
                            "properties": tool.parameters_schema,
                            "required": [name for name, config in tool.parameters_schema.items() 
                                       if "default" not in config]
                        }
                    }
                }
                schemas.append(schema)
        return schemas
    
    def _execute_tool(self, tool_name: str, **kwargs):
        """Execute a game action"""
        try:
            if tool_name == "move_drone":
                direction = kwargs.get("direction", "forward")
                return self.game.move(direction)
            elif tool_name == "turn_drone":
                direction = kwargs.get("direction", "left")
                return self.game.turn(direction)
            elif tool_name == "take_picture_drone":
                return self.game.take_picture()
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Error executing {tool_name}: {e}"
    
    def process_command(self, natural_language_command: str, debug: bool = False) -> str:
        """
        Process a natural language command and execute the appropriate game action
        """
        if debug:
            print(f"- Drone Command: {natural_language_command}")
            print(f"- Available tools: {[tool.__name__ for tool in self.tools]}")
        
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

Analyze the situation and choose the best action. Explain your reasoning first, then use the appropriate tool.
"""
        
        try:
            # Get tool schemas
            tool_schemas = self._get_tool_schemas()
            
            # Get LLM response
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.1,
                tools=tool_schemas
            )
            
            message = response.choices[0].message
            llm_response = message.content or ""
            result = ""
            
            # Handle tool calls if present
            if hasattr(message, 'tool_calls') and message.tool_calls:
                if debug:
                    print(f"- Tools called: {[tc.function.name for tc in message.tool_calls]}")
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if debug:
                        print(f"- Executing {function_name} with args: {function_args}")
                    
                    # Execute the tool
                    tool_result = self._execute_tool(function_name, **function_args)
                    result = tool_result
                    
                    if debug:
                        print(f"- Tool result: {tool_result}")
                    
                    # Record action in history
                    self.action_history.append({
                        "command": natural_language_command,
                        "action": f"{function_name}({function_args})",
                        "result": result
                    })
                
                # Generate final response based on action result
                final_prompt = f"""
You executed the action and got this result: {result}

Based on the action result, provide a brief summary of what happened and any observations about the current situation.
"""
                
                try:
                    final_response = litellm.completion(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": self.get_system_prompt()},
                            {"role": "user", "content": final_prompt}
                        ],
                        max_tokens=150,
                        temperature=0.1
                    )
                    
                    final_summary = final_response.choices[0].message.content
                    final_answer = f"LLM Reasoning: {llm_response}\n\nAction Executed: {result}\n\nSummary: {final_summary}"
                    
                    if debug:
                        print(f"- Final Answer: {final_answer}")
                    
                    return final_answer
                except:
                    final_answer = f"LLM Reasoning: {llm_response}\n\nAction Result: {result}"
                    
                    if debug:
                        print(f"- Final Answer: {final_answer}")
                    
                    return final_answer
            else:
                result = "No action taken - please provide a clearer command"
                final_answer = f"LLM Reasoning: {llm_response}\n\nAction Result: {result}"
                
                if debug:
                    print(f"- Final Answer (no tools used): {final_answer}")
                
                return final_answer
            
        except Exception as e:
            return f"Error: {e}. Please check your model configuration."


class StrategicPlanningAgent:
    """
    An agent that provides high-level strategic planning for the drone safari game
    """
    
    def __init__(self, model: str = "gemini/gemini-1.5-flash"):
        self.model = model
    
    def get_system_prompt(self) -> str:
        """System prompt for strategic planning"""
        return """You are a strategic planning AI for drone safari photography missions.

Your role: Analyze the game state and provide high-level strategic decisions.

ANALYZE:
1. Current drone position and facing direction
2. Locations of all animals (Z=zebra, E=elephant, O=oryx)
3. Obstacles (T=trees) and their positions
4. Pictures remaining and animals already photographed
5. Optimal routes and priorities

STRATEGIC DECISIONS:
- Which animal to target next and why
- Safest route to reach the target
- How to position for the perfect photo (2 cells away, facing the animal)
- Risk assessment for different approaches

COMMUNICATION:
Provide clear, actionable commands in natural language that the drone agent can execute.
Focus on one specific action or movement at a time.

Examples of good commands:
- "Move forward twice to get closer to the zebra"
- "Turn left to face the elephant"
- "Navigate around the trees to reach the oryx safely"
- "Position yourself 2 cells south of the zebra and face north for the photo"
"""
    
    def decide_next_action(self, game: DroneSafariGame) -> str:
        """Decide the next strategic action for the game"""
        # Get current game state
        status = game.get_status()
        
        # Create strategic analysis prompt
        game_state = f"""Current Game State:
- Drone Position: {status['position']}
- Facing Direction: {status['facing']}
- Pictures Remaining: {status['pictures_remaining']}/5
- Animals Photographed: {status['animals_photographed']}

Grid Layout:
{game.get_grid_string()}

Analyze this situation and provide the next strategic action as a clear natural language command.
"""
        
        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": game_state}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Strategic planning error: {e}"


class MultiAgentSystem:
    """
    A multi-agent system that coordinates strategic planning and drone control
    """
    
    def __init__(self, game: DroneSafariGame, model: str = "gemini/gemini-1.5-flash"):
        self.game = game
        self.strategic_agent = StrategicPlanningAgent(model)
        self.drone_agent = DroneAgent(game, model)
        self.step_log = []
    
    def run_autonomous_game(self, max_steps: int = 50, show_steps: bool = False) -> Dict[str, Any]:
        """Run the game autonomously using coordinated agents"""
        step_count = 0
        
        while not self.game.game_over and step_count < max_steps:
            step_count += 1
            
            # Strategic agent decides what to do
            strategic_decision = self.strategic_agent.decide_next_action(self.game)
            
            if show_steps:
                print(f"\nStep {step_count}:")
                print(f"Strategic Decision: {strategic_decision}")
            
            # Drone agent executes the decision
            execution_result = self.drone_agent.process_command(strategic_decision)
            
            if show_steps:
                print(f"Execution Result: {execution_result}")
                self.game.visualize()
            
            # Log the step
            self.step_log.append({
                "step": step_count,
                "strategic_decision": strategic_decision,
                "execution_result": execution_result,
                "game_state": self.game.get_status()
            })
            
            # Check if game ended
            if self.game.game_over:
                break
        
        # Return final results
        final_status = self.game.get_status()
        return {
            "success": all(final_status["animals_photographed"].values()),
            "steps_taken": step_count,
            "pictures_used": 5 - final_status["pictures_remaining"],
            "animals_photographed": final_status["animals_photographed"],
            "final_status": final_status,
            "step_log": self.step_log
        }
    
    def get_performance_summary(self) -> str:
        """Get a summary of the multi-agent system performance"""
        if not self.step_log:
            return "No steps recorded yet."
        
        final_status = self.game.get_status()
        success = all(final_status["animals_photographed"].values())
        
        summary = f"""Multi-Agent Performance Summary:
- Game Success: {success}
- Total Steps: {len(self.step_log)}
- Pictures Used: {5 - final_status['pictures_remaining']}/5
- Animals Photographed: {sum(final_status['animals_photographed'].values())}/3
- Strategic Planning: {len([s for s in self.step_log if 'strategic_decision' in s])} decisions made
- Execution Efficiency: {len(self.step_log)} steps for {sum(final_status['animals_photographed'].values())} photos
"""
        return summary
