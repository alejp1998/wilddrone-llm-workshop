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


class LLMAgent:
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
        response, debug_output = self.chat_with_debug(user_message, debug, clear_memory)
        if debug:
            for line in debug_output:
                print(line)
        return response

    def chat_with_debug(self, user_message: str, debug: bool = True, clear_memory: bool = True) -> tuple:
        """
        Process user message and potentially call tools, returning debug info
        
        Args:
            user_message: The message from the user
            debug: Whether to collect debug information
            clear_memory: Whether to clear conversation history before processing (default: False)
            
        Returns:
            tuple: (final_response, debug_output) where debug_output is a list of debug messages
        """
        debug_output = []
        
        if debug:
            debug_output.append(f"- User said: {user_message}")
            debug_output.append(f"- Available tools: {[tool.__name__ for tool in self.tools]}")
        
        # Clear conversation history if requested
        if clear_memory:
            self.conversation_history = []
            # if debug:
            #     debug_output.append("- Conversation memory cleared")
        
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
                temperature=0.0,
                tools=tool_schemas if tool_schemas else None
            )
            
            # Check if response has choices
            if not response.choices or len(response.choices) == 0:
                error_msg = "Error: No response choices returned from LLM"
                if debug:
                    debug_output.append(error_msg)
                return error_msg, debug_output
            
            message = response.choices[0].message
            response_text = message.content or ""
            
            # Handle tool calls if present
            if hasattr(message, 'tool_calls') and message.tool_calls:
                if debug:
                    debug_output.append(f"- Tools called: {[tc.function.name for tc in message.tool_calls]}")
                
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
                        debug_output.append(f"- Executing {function_name} with args: {function_args}")
                    
                    # Execute the tool
                    tool_result = self._execute_tool(function_name, **function_args)
                    
                    if debug:
                        debug_output.append(f"- Tool result: {tool_result}")
                    
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
                
                # Check if final response has choices
                if not final_response.choices or len(final_response.choices) == 0:
                    error_msg = "Error: No response choices returned from final LLM call"
                    if debug:
                        debug_output.append(error_msg)
                    return error_msg, debug_output
                
                final_response_text = final_response.choices[0].message.content
                
                if debug:
                    debug_output.append(f"- Final Answer: {final_response_text}")
                
                # Add final response to history
                self.conversation_history.append({"role": "assistant", "content": final_response_text})
                return final_response_text, debug_output
            else:
                # No tool calls, return original response
                if debug:
                    debug_output.append(f"- Final Answer (no tools used): {response_text}")
                
                self.conversation_history.append({"role": "assistant", "content": response_text})
                return response_text, debug_output
            
        except Exception as e:
            error_msg = f"Error: {e}. Please check your model configuration."
            debug_output.append(error_msg)
            return error_msg, debug_output