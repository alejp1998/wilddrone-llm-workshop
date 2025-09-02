import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import ListedColormap
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import os

# Game configuration
GRID_SIZE = 20
EMPTY = 0
TREE = 1
ZEBRA = 2
ELEPHANT = 3
ORYX = 4

# Direction mappings
DIRECTIONS = {
    'North': (1, 0),
    'East': (0, 1),
    'South': (-1, 0),
    'West': (0, -1)
}

MOVE_DIRECTIONS = {
    'f': 'forward',
    'l': 'left', 
    'r': 'right',
    'b': 'back'
}

def load_icon(filename, zoom=0.1):
    """Load an icon image and return it as an OffsetImage"""
    try:
        img_path = os.path.join('images', filename)
        img = mpimg.imread(img_path)
        return img
    except Exception as e:
        print(f"Warning: Could not load {filename}: {e}")
        return None

def add_icon_to_plot(ax, x, y, icon, zorder=1):
    """Add an icon to the plot at the specified coordinates."""
    if icon is not None:
        icon_bbox = OffsetImage(icon, zoom=0.06)
        annotation = AnnotationBbox(icon_bbox, (x, y), frameon=False, zorder=zorder)
        ax.add_artist(annotation)


class DroneSafariGame:
    def __init__(self):
        self.grid = np.zeros((GRID_SIZE, GRID_SIZE))
        self.drone_pos = [10, 10]  # Start in middle of grid
        self.drone_facing = 'North'  # Can be North, East, South, West
        self.animals_photographed = {'zebra': False, 'elephant': False, 'oryx': False}
        self.pictures_remaining = 5  # Limited number of pictures
        self.pictures_taken = 0
        self.total_moves = 0  # Track total number of moves
        self.total_turns = 0  # Track total number of turns
        self.photographed_locations = {}  # Track (row, col): picture_number for visualization
        self.scared_animals = set()  # Track positions where animals were scared away
        self.game_over = False
        self.game_won = False
        self.failure_reason = None  # Track specific failure reason
        self.message = "Game started! Navigate carefully. You can take up to 5 pictures."
        
        self._setup_grid()
        
    def _setup_grid(self):
        """Initialize the grid with trees and animals"""
        # Add some trees randomly
        tree_positions = [
            (3, 5), (7, 12), (15, 8), (2, 17), (18, 3),
            (9, 2), (14, 15), (6, 9), (11, 18), (4, 14),
            (16, 6), (8, 16), (12, 4), (5, 11), (17, 13)
        ]
        
        for pos in tree_positions:
            if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                self.grid[pos] = TREE
        
        # Place animals in safe positions (not too close to trees or drone)
        animal_positions = {
            ZEBRA: (5, 5),
            ELEPHANT: (15, 15), 
            ORYX: (3, 15)
        }
        
        for animal, pos in animal_positions.items():
            self.grid[pos] = animal
            
    def _is_valid_position(self, row, col):
        """Check if position is within grid bounds"""
        return 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE
    
    def _is_adjacent_to_animal(self, row, col):
        """Check if position is adjacent to any animal"""
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                check_row, check_col = row + dr, col + dc
                if (self._is_valid_position(check_row, check_col) and 
                    self.grid[check_row, check_col] in [ZEBRA, ELEPHANT, ORYX]):
                    return True
        return False
    
    def _get_relative_direction(self, direction):
        """Convert relative direction to absolute direction based on current facing"""
        facing_index = list(DIRECTIONS.keys()).index(self.drone_facing)
        
        if direction == 'forward':
            return self.drone_facing
        elif direction == 'back':
            return list(DIRECTIONS.keys())[(facing_index + 2) % 4]
        elif direction == 'right':
            return list(DIRECTIONS.keys())[(facing_index + 1) % 4]
        elif direction == 'left':
            return list(DIRECTIONS.keys())[(facing_index - 1) % 4]
        
        return (0, 0)  # No movement

    # Tool methods
    def move(self, direction):
        """Move the drone in the specified direction"""
        if self.game_over:
            return "Game is over! Reset to play again."
        
        if direction not in MOVE_DIRECTIONS:
            return f"Invalid direction: {direction}. Use: {list(MOVE_DIRECTIONS.keys())}"
        
        move_type = MOVE_DIRECTIONS[direction]
        
        # Get the movement delta
        absolute_dir = self._get_relative_direction(move_type)
        if isinstance(absolute_dir, str):
            dr, dc = DIRECTIONS[absolute_dir]
        else:
            dr, dc = absolute_dir
        
        new_row = self.drone_pos[0] + dr
        new_col = self.drone_pos[1] + dc
        
        # Check boundaries
        if not self._is_valid_position(new_row, new_col):
            self.drone_pos = [new_row, new_col]  # Update position to show crash location
            self.game_over = True
            self.failure_reason = "boundary_crash"
            self.message = "Drone crashed! Flew outside the grid boundaries."
            return self.message
        
        # Check for collision with tree
        if self.grid[new_row, new_col] == TREE:
            self.drone_pos = [new_row, new_col]  # Update position to show crash location
            self.game_over = True
            self.failure_reason = "tree_crash"
            self.message = "Drone crashed into a tree!"
            return self.message
        
        # Check for collision with animal
        if self.grid[new_row, new_col] in [ZEBRA, ELEPHANT, ORYX]:
            self.drone_pos = [new_row, new_col]  # Update position to show crash location
            self.game_over = True
            self.failure_reason = "animal_crash"
            self.message = "Drone crashed into an animal!"
            return self.message
        
        # Check if too close to animal
        if self._is_adjacent_to_animal(new_row, new_col):
            # Find which animal was scared and mark its position
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    check_row, check_col = new_row + dr, new_col + dc
                    if (self._is_valid_position(check_row, check_col) and 
                        self.grid[check_row, check_col] in [ZEBRA, ELEPHANT, ORYX]):
                        # Mark this position as having a scared animal
                        self.scared_animals.add((check_row, check_col))
                        # Remove the animal from the grid (it ran away)
                        self.grid[check_row, check_col] = EMPTY
            
            self.drone_pos = [new_row, new_col]  # Update position to show crash location
            self.game_over = True
            self.failure_reason = "scared_animal"
            self.message = "Drone got too close to an animal and scared it away!"
            return self.message
        
        # Move is valid
        self.drone_pos = [new_row, new_col]
        self.total_moves += 1  # Increment move counter
        self.message = f"Moved {move_type} to position ({new_row}, {new_col})"
        return self.message
    
    def turn(self, direction):
        """Turn the drone left or right"""
        if self.game_over:
            return "Game is over! Reset to play again."
        
        if direction not in ['left', 'right']:
            return "Invalid turn direction. Use 'left' or 'right'."
        
        facing_index = list(DIRECTIONS.keys()).index(self.drone_facing)
        
        if direction == 'right':
            new_facing_index = (facing_index - 1) % 4
        else:  # right
            new_facing_index = (facing_index + 1) % 4
        
        self.drone_facing = list(DIRECTIONS.keys())[new_facing_index]
        self.total_turns += 1  # Increment turn counter
        self.message = f"Turned {direction}, now facing {self.drone_facing}"
        return self.message
    
    def take_picture(self):
        """Attempt to take a picture of an animal"""
        if self.game_over:
            return "Game is over! Reset to play again."
        
        # Check if there are pictures remaining
        if self.pictures_remaining <= 0:
            self.message = "No pictures remaining! You've used all 5 pictures."
            self.game_over = True
            return self.message
        
        # Use one picture
        self.pictures_remaining -= 1
        self.pictures_taken += 1
        
        # Check if there's an animal exactly 2 cells away in the facing direction
        dr, dc = DIRECTIONS[self.drone_facing]
        target_row = self.drone_pos[0] + 2 * dr
        target_col = self.drone_pos[1] + 2 * dc
        
        # Record the photographed location for visualization (regardless of what's there)
        if self._is_valid_position(target_row, target_col):
            self.photographed_locations[(target_row, target_col)] = self.pictures_taken
        
        # Check if target is out of bounds
        if not self._is_valid_position(target_row, target_col):
            self.message = f"Picture #{self.pictures_taken} wasted! No animal in range to photograph. {self.pictures_remaining} pictures remaining."
            if self.pictures_remaining == 0:
                self.game_over = True
                self.message += " Game Over - No pictures left!"
            return self.message
        
        animal_value = self.grid[target_row, target_col]
        
        # Check what's at the target location
        if animal_value == ZEBRA:
            if self.animals_photographed['zebra']:
                self.message = f"Picture #{self.pictures_taken} wasted! Zebra already photographed. {self.pictures_remaining} pictures remaining."
            else:
                self.animals_photographed['zebra'] = True
                self.message = f"Picture #{self.pictures_taken}: Successfully photographed the zebra! {self.pictures_remaining} pictures remaining."
        elif animal_value == ELEPHANT:
            if self.animals_photographed['elephant']:
                self.message = f"Picture #{self.pictures_taken} wasted! Elephant already photographed. {self.pictures_remaining} pictures remaining."
            else:
                self.animals_photographed['elephant'] = True
                self.message = f"Picture #{self.pictures_taken}: Successfully photographed the elephant! {self.pictures_remaining} pictures remaining."
        elif animal_value == ORYX:
            if self.animals_photographed['oryx']:
                self.message = f"Picture #{self.pictures_taken} wasted! Oryx already photographed. {self.pictures_remaining} pictures remaining."
            else:
                self.animals_photographed['oryx'] = True
                self.message = f"Picture #{self.pictures_taken}: Successfully photographed the oryx! {self.pictures_remaining} pictures remaining."
        else:
            # Nothing to photograph or tree/empty space
            if animal_value == TREE:
                self.message = f"Picture #{self.pictures_taken} wasted! You photographed a tree. {self.pictures_remaining} pictures remaining."
            else:
                self.message = f"Picture #{self.pictures_taken} wasted! No animal in range to photograph. {self.pictures_remaining} pictures remaining."
        
        # Check if all animals are photographed
        if all(self.animals_photographed.values()):
            self.game_won = True
            self.game_over = True
            self.message += " Congratulations! You've photographed all animals and won the game!"
        # Check if no pictures left but game not won
        elif self.pictures_remaining == 0:
            self.game_over = True
            self.failure_reason = "out_of_pictures"
            self.message += " Game Over - No pictures left and mission incomplete!"
        
        return self.message

    def get_status(self):
        """Get current game status"""
        status = {
            'position': self.drone_pos,
            'facing': self.drone_facing,
            'animals_photographed': self.animals_photographed,
            'pictures_remaining': self.pictures_remaining,
            'pictures_taken': self.pictures_taken,
            'total_moves': self.total_moves,
            'total_turns': self.total_turns,
            'photographed_locations': self.photographed_locations,
            'game_over': self.game_over,
            'game_won': self.game_won,
            'message': self.message
        }
        return status
    
    def reset_game(self):
        """Reset the game to initial state"""
        self.__init__()
        return "Game reset! Ready to start again."
    
    def visualize(self, figsize=(12, 10)):
        """Visualize the current game state"""
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create a copy of the grid for visualization (empty background)
        vis_grid = np.zeros((GRID_SIZE, GRID_SIZE))
        
        # Create colormap for background (just white)
        colors = ['white']  # only white background
        cmap = ListedColormap(colors)
        
        # Display the background grid (invisible since it's all white)
        im = ax.imshow(vis_grid, cmap=cmap, vmin=0, vmax=0)
        
        # Load icons
        tree_icon = load_icon('tree.png', zoom=0.06)
        zebra_icon = load_icon('zebra.png', zoom=0.06)
        elephant_icon = load_icon('elephant.png', zoom=0.06)
        oryx_icon = load_icon('oryx.png', zoom=0.06)
        drone_icon = load_icon('drone.png', zoom=0.06)
        crashed_drone_icon = load_icon('crashed_drone.png', zoom=0.06)
        scared_animal_icon = load_icon('scared_animal.png', zoom=0.06)
        
        # Add icons for trees and animals
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                cell_value = self.grid[row, col]
                
                if cell_value == TREE:
                    add_icon_to_plot(ax, col, row, tree_icon, zorder=5)
                    if tree_icon is None:
                        # Fallback: brown square
                        square = patches.Rectangle((col-0.4, row-0.4), 0.8, 0.8, 
                                                 color='brown', zorder=5)
                        ax.add_patch(square)
                elif cell_value == ZEBRA:
                    add_icon_to_plot(ax, col, row, zebra_icon, zorder=6)
                    if zebra_icon is None:
                        # Fallback: black square
                        square = patches.Rectangle((col-0.4, row-0.4), 0.8, 0.8, 
                                                 color='black', zorder=5)
                        ax.add_patch(square)
                elif cell_value == ELEPHANT:
                    add_icon_to_plot(ax, col, row, elephant_icon, zorder=6)
                    if elephant_icon is None:
                        # Fallback: gray square
                        square = patches.Rectangle((col-0.4, row-0.4), 0.8, 0.8, 
                                                 color='gray', zorder=5)
                        ax.add_patch(square)
                elif cell_value == ORYX:
                    add_icon_to_plot(ax, col, row, oryx_icon, zorder=6)
                    if oryx_icon is None:
                        # Fallback: orange square
                        square = patches.Rectangle((col-0.4, row-0.4), 0.8, 0.8, 
                                                 color='orange', zorder=5)
                        ax.add_patch(square)
        
        # Add scared animal icons at their positions
        for (scared_row, scared_col) in self.scared_animals:
            add_icon_to_plot(ax, scared_col, scared_row, scared_animal_icon, zorder=7)
            if scared_animal_icon is None:
                # Fallback: red square with exclamation
                square = patches.Rectangle((scared_col-0.4, scared_row-0.4), 0.8, 0.8, 
                                         color='red', alpha=0.7, zorder=7)
                ax.add_patch(square)
                ax.text(scared_col, scared_row, '!', ha='center', va='center', 
                       fontsize=16, fontweight='bold', color='white', zorder=8)
        
        # Add drone position and facing direction
        drone_row, drone_col = self.drone_pos
        
        # Check if drone position is outside grid bounds (for boundary crashes)
        drone_visible = (0 <= drone_row < GRID_SIZE and 0 <= drone_col < GRID_SIZE)
        
        if self.game_over and not self.game_won and self.failure_reason != "scared_animal":
            # Show crashed drone (but not when animal was scared)
            if drone_visible:
                # Try to use crashed drone icon, fallback to red circle with exclamation
                if crashed_drone_icon is not None:
                    add_icon_to_plot(ax, drone_col, drone_row, crashed_drone_icon, zorder=10)
                else:
                    # Fallback: Draw crashed drone as a red circle
                    circle = patches.Circle((drone_col, drone_row), 0.35, color='darkred', zorder=10)
                    ax.add_patch(circle)
                    # Add exclamation mark
                    ax.text(drone_col, drone_row, '!', ha='center', va='center', 
                           fontsize=20, fontweight='bold', color='white', zorder=12)
            else:
                # For boundary crashes, show where the drone tried to go
                if drone_row < 0:
                    ax.text(drone_col, -0.8, 'CRASH!', ha='center', va='center', 
                           fontsize=12, fontweight='bold', color='red')
                elif drone_row >= GRID_SIZE:
                    ax.text(drone_col, GRID_SIZE-0.2, 'CRASH!', ha='center', va='center', 
                           fontsize=12, fontweight='bold', color='red')
                elif drone_col < 0:
                    ax.text(-0.8, drone_row, 'CRASH!', ha='center', va='center', 
                           fontsize=12, fontweight='bold', color='red', rotation=90)
                elif drone_col >= GRID_SIZE:
                    ax.text(GRID_SIZE-0.2, drone_row, 'CRASH!', ha='center', va='center', 
                           fontsize=12, fontweight='bold', color='red', rotation=90)
        else:
            # Draw normal drone (including when game is over due to scared animal)
            if drone_visible:
                # Try to use drone icon, fallback to blue circle with arrow
                if drone_icon is not None:
                    add_icon_to_plot(ax, drone_col, drone_row, drone_icon, zorder=10)
                    # Add facing direction indicator (small arrow overlay)
                    dr, dc = DIRECTIONS[self.drone_facing]
                    ax.arrow(drone_col, drone_row, dc*0.7, dr*0.7, 
                            head_width=0.15, head_length=0.12, fc='red', ec='red', zorder=11, linewidth=2)
                else:
                    # Fallback: Draw normal drone in blue
                    circle = patches.Circle((drone_col, drone_row), 0.3, color='blue', zorder=10)
                    ax.add_patch(circle)
                    
                    # Draw facing direction arrow (only if not crashed)
                    dr, dc = DIRECTIONS[self.drone_facing]
                    ax.arrow(drone_col, drone_row, dc*0.7, dr*0.7, 
                            head_width=0.15, head_length=0.12, fc='blue', ec='blue', zorder=11, linewidth=2)
        
        # Draw photo markers for all photographed locations
        for (photo_row, photo_col), picture_num in self.photographed_locations.items():
            # Draw blue cross
            ax.plot([photo_col-0.3, photo_col+0.3], [photo_row, photo_row], 'b-', linewidth=3, zorder=12)
            ax.plot([photo_col, photo_col], [photo_row-0.3, photo_row+0.3], 'b-', linewidth=3, zorder=12)
            # Add picture number in white circle
            circle = patches.Circle((photo_col, photo_row), 0.15, color='white', zorder=13, edgecolor='blue', linewidth=2)
            ax.add_patch(circle)
            ax.text(photo_col, photo_row, str(picture_num), ha='center', va='center', 
                   fontsize=8, fontweight='bold', color='blue', zorder=14)
        
        # Add cell boundary grid lines only
        # Draw cell boundaries as thin lines
        for i in range(GRID_SIZE + 1):
            ax.axhline(y=i-0.5, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
            ax.axvline(x=i-0.5, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
        
        # Set proper limits to ensure all grid lines are visible
        ax.set_xlim(-0.5, GRID_SIZE-0.5)
        ax.set_ylim(-0.5, GRID_SIZE-0.5)
        
        # Labels and title with enhanced styling
        ax.set_xlabel('Column →', fontsize=12, fontweight='bold')
        ax.set_ylabel('← Row', fontsize=12, fontweight='bold')
        
        # Dynamic title with matplotlib-compatible formatting
        if self.game_over:
            if self.game_won:
                title = 'MISSION ACCOMPLISHED!\nALL ANIMALS PHOTOGRAPHED!'
                title_color = 'darkgreen'
            else:
                # Different titles based on failure reason
                if self.failure_reason == "scared_animal":
                    title = 'MISSION FAILED!\nANIMAL SCARED AWAY!'
                elif self.failure_reason == "out_of_pictures":
                    title = 'MISSION FAILED!\nRAN OUT OF PICTURES!'
                elif self.failure_reason == "boundary_crash":
                    title = 'MISSION FAILED!\nDRONE CRASHED!'
                elif self.failure_reason == "tree_crash":
                    title = 'MISSION FAILED!\nHIT A TREE!'
                elif self.failure_reason == "animal_crash":
                    title = 'MISSION FAILED!\nSCARED AN ANIMAL!'
                else:
                    title = 'MISSION FAILED!\nDRONE CRASHED!'
                title_color = 'darkred'
        else:
            title = f'DRONE SAFARI MISSION\nPosition: {self.drone_pos} | Facing: {self.drone_facing}'
            title_color = 'darkblue'
        
        ax.set_title(title, fontsize=14, fontweight='bold', color=title_color)
        
        # Add enhanced status text with matplotlib-compatible formatting
        status_text = "MISSION STATUS\n" + "="*30 + "\n\n"
        
        # Pictures remaining
        status_text += f"PICTURES: {self.pictures_remaining}/5 remaining ({self.pictures_taken} used)\n"
        
        # Movement statistics
        status_text += f"MOVES: {self.total_moves} | TURNS: {self.total_turns}\n\n"
        
        # Animals with clear text presentation
        status_text += "PHOTO COLLECTION:\n"
        animals_info = [
            ('zebra', 'Z', 'ZEBRA'),
            ('elephant', 'E', 'ELEPHANT'), 
            ('oryx', 'O', 'ORYX')
        ]
        
        for animal, symbol, name in animals_info:
            photographed = self.animals_photographed[animal]
            if photographed:
                status_text += f"[{symbol}] {name}: CAPTURED!\n"
            else:
                status_text += f"[{symbol}] {name}: MISSING\n"
        
        # Progress visualization with text
        total_animals = len(self.animals_photographed)
        captured = sum(self.animals_photographed.values())
        progress = "█" * captured + "░" * (total_animals - captured)
        status_text += f"\nMission Progress:\n[{progress}] {captured}/{total_animals} animals\n\n"
        
        # Latest action with clear formatting
        message = self.message
        if len(message) > 120:  # Increased from 80 to allow longer messages
            message = message[:117] + "..."
        
        status_text += "="*30 + "\n"
        if self.game_over:
            if self.game_won:
                status_text += "MISSION COMPLETE!\n"
            else:
                status_text += "MISSION FAILED!\n"
        else:
            status_text += "LATEST ACTION:\n"
        status_text += f"> {message}"
        
        # Enhanced text box with dynamic colors and better positioning
        box_color = 'lightblue' if self.game_won else ('lightgreen' if not self.game_over else 'lightcoral')
        plt.figtext(0.02, 0.01, status_text, fontsize=10, verticalalignment='bottom',
                    fontweight='bold', wrap=True, 
                    bbox=dict(boxstyle="round,pad=0.6", facecolor=box_color, alpha=0.9,
                             edgecolor='black', linewidth=2))
        
        # Set axis ticks to show numbers every 2 units (0, 2, 4, 6, ...)
        ax.set_xticks(range(0, GRID_SIZE, 2))
        ax.set_yticks(range(0, GRID_SIZE, 2))
        
        # Adjust layout to leave more space at bottom for text
        plt.subplots_adjust(bottom=0.3)
        plt.show()
        
        return fig
        
    def print_instructions(self):
        """Print game instructions"""
        instructions = """
DRONE SAFARI GAME INSTRUCTIONS

OBJECTIVE: Photograph all three animals (zebra, elephant, oryx) with only 5 pictures!

AVAILABLE TOOLS:
1. move(direction) - Move the drone one cell
   Directions: 'f'=forward, 'l'=left, 'r'=right, 'b'=back

2. turn(direction) - Change facing direction
   Directions: 'left' or 'right'

3. take_picture() - Photograph an animal (LIMITED TO 5 PICTURES TOTAL!)
   Only works when exactly 2 cells away from an animal in the facing direction
   Wasted pictures count against your limit!

INTERACTIVE CONTROLS (when running the script):
• Arrow Keys: Move drone (↑=forward, ↓=back, ←=left, →=right)
• A/D Keys: Turn right/left
• Enter: Take picture
• R: Reset game

RULES:
• Don't crash into trees (brown squares)
• Don't get too close to animals (adjacent cells)
• Don't fly outside the grid boundaries
• Maintain safe distance from animals to avoid scaring them
• You only have 5 pictures - use them wisely!
• Taking pictures of empty space, trees, or already-photographed animals wastes pictures!
• The game tracks your total moves and turns for performance evaluation

GRID LEGEND:
• White = Empty space
• Brown = Trees (obstacles)
• Black = Zebra
• Gray = Elephant  
• Orange = Oryx
• Blue circle with arrow = Your drone (arrow shows facing direction)
• Red circle with ! = Crashed drone
• Scared animal icon = Animal that was scared away (mission failed)
• Blue cross with number = Photo marker (shows where pictures were taken)
        """
        print(instructions)


def process_natural_language_command(command, game):
    """
    Process a natural language command and execute the appropriate game action.
    
    This is where you would implement the LLM's natural language understanding
    to map user intentions to specific tool calls.
    
    Args:
        command (str): Natural language command from the user
        game (DroneSafariGame): The game instance
    
    Returns:
        str: Result of the executed command
    """
    command = command.lower().strip()
    
    # Simple keyword-based mapping (you can make this more sophisticated with LLM)
    if 'forward' in command or 'ahead' in command:
        return game.move('f')
    elif 'back' in command or 'backward' in command:
        return game.move('b')
    elif 'left' in command and 'turn' in command:
        return game.turn('left')
    elif 'right' in command and 'turn' in command:
        return game.turn('right')
    elif 'left' in command:
        return game.move('l')
    elif 'right' in command:
        return game.move('r')
    elif 'picture' in command or 'photo' in command or 'take' in command:
        return game.take_picture()
    else:
        return f"I don't understand the command: '{command}'. Try commands like 'move forward', 'turn left', or 'take picture'."


class InteractiveDroneSafariGame:
    """Interactive version of the drone safari game with keyboard controls"""
    
    def __init__(self):
        self.game = DroneSafariGame()
        self.fig = None
        self.ax = None
        self.running = True
        
    def on_key_press(self, event):
        """Handle keyboard input"""
        if not self.running:
            return
        
        result = ""
        
        # If game is over, allow restart with any action key or quit with q
        if self.game.game_over:
            if event.key == 'q':
                self.running = False
                plt.close(self.fig)
                return
            elif event.key in ['up', 'down', 'left', 'right', 'a', 'd', 'enter', 'r']:
                # Restart game with any action key
                self.game = DroneSafariGame()
                result = "Game restarted! Ready to play again."
                print(f"Action result: {result}")
                self.update_display()
                return
            else:
                return  # Ignore other keys when game is over
        
        # Normal gameplay controls
        # Arrow keys for movement
        if event.key == 'up':
            result = self.game.move('f')  # Forward
        elif event.key == 'down':
            result = self.game.move('b')  # Back
        elif event.key == 'left':
            result = self.game.move('l')  # Left
        elif event.key == 'right':
            result = self.game.move('r')  # Right
        
        # A and D keys for turning
        elif event.key == 'a':
            result = self.game.turn('right')
        elif event.key == 'd':
            result = self.game.turn('left')
        
        # Enter key for taking pictures
        elif event.key == 'enter':
            result = self.game.take_picture()
        
        # R key for reset (during gameplay)
        elif event.key == 'r':
            self.game = DroneSafariGame()
            result = "Game reset! Ready to start again."
            
        # Q key for quit
        elif event.key == 'q':
            self.running = False
            plt.close(self.fig)
            return
            
        # ESC key for quit
        elif event.key == 'escape':
            self.running = False
            plt.close(self.fig)
            return
        
        # Update display if a valid command was executed
        if result:
            # Make terminal output more flashy
            print("="*50)
            if "Successfully photographed" in result:
                print("📸 *** PHOTO CAPTURED! *** 📸")
                print(f"🎯 {result}")
            elif "crashed" in result.lower() or "game over" in result.lower():
                print("💥 *** MISSION FAILED! *** 💥")
                print(f"🚨 {result}")
            elif "reset" in result.lower() or "restart" in result.lower():
                print("🔄 *** MISSION RESTARTED! *** 🔄")
                print(f"🚁 {result}")
            elif "Moved" in result:
                print("🚁 *** DRONE MOVING *** 🚁")
                print(f"📍 {result}")
            elif "Turned" in result:
                print("🧭 *** DRONE TURNING *** 🧭")
                print(f"🔄 {result}")
            else:
                print(f"📡 ACTION RESULT: {result}")
            print("="*50)
            
            self.update_display()
            
            # Check for game over with enhanced feedback
            if self.game.game_over:
                if self.game.game_won:
                    print("\n" + "🎉"*20)
                    print("🏆 *** CONGRATULATIONS! YOU WON! *** 🏆")
                    print("🎯 You've successfully photographed all animals!")
                    print("🔄 Press any action key to play again or 'Q' to quit.")
                    print("🎉"*20)
                else:
                    print("\n" + "💥"*20)
                    print("🚨 *** MISSION FAILED! *** 🚨")
                    print("🔄 Press any action key to restart or 'Q' to quit.")
                    print("💥"*20)
    
    def update_display(self):
        """Update the game visualization"""
        if not self.fig or not self.ax:
            return
            
        self.ax.clear()
        
        # Create a copy of the grid for visualization (empty background)
        vis_grid = np.zeros((GRID_SIZE, GRID_SIZE))
        
        # Create colormap for background (just white)
        colors = ['white']  # only white background
        cmap = ListedColormap(colors)
        
        # Display the background grid (invisible since it's all white)
        im = self.ax.imshow(vis_grid, cmap=cmap, vmin=0, vmax=0)
        
        # Load icons
        tree_icon = load_icon('tree.png', zoom=0.05)
        zebra_icon = load_icon('zebra.png', zoom=0.05)
        elephant_icon = load_icon('elephant.png', zoom=0.05)
        oryx_icon = load_icon('oryx.png', zoom=0.05)
        drone_icon = load_icon('drone.png', zoom=0.05)
        crashed_drone_icon = load_icon('crashed_drone.png', zoom=0.05)
        scared_animal_icon = load_icon('scared_animal.png', zoom=0.05)
        
        # Add icons for trees and animals
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                cell_value = self.game.grid[row, col]
                
                if cell_value == TREE:
                    add_icon_to_plot(self.ax, col, row, tree_icon, zorder=5)
                    if tree_icon is None:
                        # Fallback: brown square
                        square = patches.Rectangle((col-0.4, row-0.4), 0.8, 0.8, 
                                                 color='brown', zorder=5)
                        self.ax.add_patch(square)
                elif cell_value == ZEBRA:
                    add_icon_to_plot(self.ax, col, row, zebra_icon, zorder=6)
                    if zebra_icon is None:
                        # Fallback: black square
                        square = patches.Rectangle((col-0.4, row-0.4), 0.8, 0.8, 
                                                 color='black', zorder=5)
                        self.ax.add_patch(square)
                elif cell_value == ELEPHANT:
                    add_icon_to_plot(self.ax, col, row, elephant_icon, zorder=6)
                    if elephant_icon is None:
                        # Fallback: gray square
                        square = patches.Rectangle((col-0.4, row-0.4), 0.8, 0.8, 
                                                 color='gray', zorder=5)
                        self.ax.add_patch(square)
                elif cell_value == ORYX:
                    add_icon_to_plot(self.ax, col, row, oryx_icon, zorder=6)
                    if oryx_icon is None:
                        # Fallback: orange square
                        square = patches.Rectangle((col-0.4, row-0.4), 0.8, 0.8, 
                                                 color='orange', zorder=5)
                        self.ax.add_patch(square)
        
        # Add scared animal icons at their positions
        for (scared_row, scared_col) in self.game.scared_animals:
            add_icon_to_plot(self.ax, scared_col, scared_row, scared_animal_icon, zorder=7)
            if scared_animal_icon is None:
                # Fallback: red square with exclamation
                square = patches.Rectangle((scared_col-0.4, scared_row-0.4), 0.8, 0.8, 
                                         color='red', alpha=0.7, zorder=7)
                self.ax.add_patch(square)
                self.ax.text(scared_col, scared_row, '!', ha='center', va='center', 
                           fontsize=16, fontweight='bold', color='white', zorder=8)
        
        # Add drone position and facing direction
        drone_row, drone_col = self.game.drone_pos
        
        # Check if drone position is outside grid bounds (for boundary crashes)
        drone_visible = (0 <= drone_row < GRID_SIZE and 0 <= drone_col < GRID_SIZE)
        
        if self.game.game_over and not self.game.game_won and self.game.failure_reason != "scared_animal":
            # Show crashed drone (but not when animal was scared)
            if drone_visible:
                # Try to use crashed drone icon, fallback to red circle with exclamation
                if crashed_drone_icon is not None:
                    add_icon_to_plot(self.ax, drone_col, drone_row, crashed_drone_icon, zorder=10)
                else:
                    # Fallback: Draw crashed drone as a red circle
                    circle = patches.Circle((drone_col, drone_row), 0.35, color='darkred', zorder=10)
                    self.ax.add_patch(circle)
                    # Add exclamation mark
                    self.ax.text(drone_col, drone_row, '!', ha='center', va='center', 
                               fontsize=20, fontweight='bold', color='white', zorder=12)
            else:
                # For boundary crashes, show where the drone tried to go
                if drone_row < 0:
                    self.ax.text(drone_col, -0.8, 'CRASH!', ha='center', va='center', 
                               fontsize=12, fontweight='bold', color='red')
                elif drone_row >= GRID_SIZE:
                    self.ax.text(drone_col, GRID_SIZE-0.2, 'CRASH!', ha='center', va='center', 
                               fontsize=12, fontweight='bold', color='red')
                elif drone_col < 0:
                    self.ax.text(-0.8, drone_row, 'CRASH!', ha='center', va='center', 
                               fontsize=12, fontweight='bold', color='red', rotation=90)
                elif drone_col >= GRID_SIZE:
                    self.ax.text(GRID_SIZE-0.2, drone_row, 'CRASH!', ha='center', va='center', 
                               fontsize=12, fontweight='bold', color='red', rotation=90)
        else:
            # Draw normal drone (including when game is over due to scared animal)
            if drone_visible:
                # Try to use drone icon, fallback to blue circle with arrow
                if drone_icon is not None:
                    add_icon_to_plot(self.ax, drone_col, drone_row, drone_icon, zorder=10)
                    # Add facing direction indicator (small arrow overlay)
                    dr, dc = DIRECTIONS[self.game.drone_facing]
                    self.ax.arrow(drone_col, drone_row, dc*0.7, dr*0.7, 
                                head_width=0.12, head_length=0.1, fc='red', ec='red', zorder=11, linewidth=2)
                else:
                    # Fallback: Draw normal drone in blue
                    circle = patches.Circle((drone_col, drone_row), 0.3, color='blue', zorder=10)
                    self.ax.add_patch(circle)
                    
                    # Draw facing direction arrow (only if not crashed)
                    dr, dc = DIRECTIONS[self.game.drone_facing]
                self.ax.arrow(drone_col, drone_row, dc*0.7, dr*0.7, 
                            head_width=0.15, head_length=0.1, fc='blue', ec='blue', zorder=11, linewidth=2)
        
        # Draw photo markers for all photographed locations
        for (photo_row, photo_col), picture_num in self.game.photographed_locations.items():
            # Draw blue cross
            self.ax.plot([photo_col-0.3, photo_col+0.3], [photo_row, photo_row], 'b-', linewidth=3, zorder=12)
            self.ax.plot([photo_col, photo_col], [photo_row-0.3, photo_row+0.3], 'b-', linewidth=3, zorder=12)
            # Add picture number in white circle
            circle = patches.Circle((photo_col, photo_row), 0.15, color='white', zorder=13, edgecolor='blue', linewidth=2)
            self.ax.add_patch(circle)
            self.ax.text(photo_col, photo_row, str(picture_num), ha='center', va='center', 
                        fontsize=8, fontweight='bold', color='blue', zorder=14)
        
        # Add cell boundary grid lines only
        # Draw cell boundaries as thin lines
        for i in range(GRID_SIZE + 1):
            self.ax.axhline(y=i-0.5, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
            self.ax.axvline(x=i-0.5, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
        
        # Set proper limits to ensure all grid lines are visible
        self.ax.set_xlim(-0.5, GRID_SIZE-0.5)
        self.ax.set_ylim(-0.5, GRID_SIZE-0.5)
        
        # Set axis ticks to show numbers every 2 units (0, 2, 4, 6, ...)
        self.ax.set_xticks(range(0, GRID_SIZE, 2))
        self.ax.set_yticks(range(0, GRID_SIZE, 2))
        
        # Labels and title
        self.ax.set_xlabel('Column')
        self.ax.set_ylabel('Row')
        
        # Dynamic title based on game state with matplotlib-compatible styling
        if self.game.game_over:
            if self.game.game_won:
                title = 'MISSION ACCOMPLISHED!\n'
                title += 'ALL ANIMALS PHOTOGRAPHED!\n'
                title += f'Final Position: {self.game.drone_pos}'
            else:
                # Different titles based on failure reason
                if self.game.failure_reason == "scared_animal":
                    title = 'MISSION FAILED!\n'
                    title += 'ANIMAL SCARED AWAY!\n'
                    title += f'Failure Position: {self.game.drone_pos}'
                elif self.game.failure_reason == "out_of_pictures":
                    title = 'MISSION FAILED!\n'
                    title += 'RAN OUT OF PICTURES!\n'
                    title += f'Final Position: {self.game.drone_pos}'
                elif self.game.failure_reason == "boundary_crash":
                    title = 'MISSION FAILED!\n'
                    title += 'BOUNDARY CRASH!\n'
                    title += f'Crash Position: {self.game.drone_pos}'
                elif self.game.failure_reason == "tree_crash":
                    title = 'MISSION FAILED!\n'
                    title += 'HIT A TREE!\n'
                    title += f'Crash Position: {self.game.drone_pos}'
                elif self.game.failure_reason == "animal_crash":
                    title = 'MISSION FAILED!\n'
                    title += 'SCARED AN ANIMAL!\n'
                    title += f'Incident Position: {self.game.drone_pos}'
                else:
                    title = 'MISSION FAILED!\n'
                    title += 'DRONE CRASHED!\n'
                    title += f'Crash Position: {self.game.drone_pos}'
        else:
            title = 'DRONE SAFARI MISSION IN PROGRESS\n'
            title += f'Position: {self.game.drone_pos} | Facing: {self.game.drone_facing}'
        
        self.ax.set_title(title, fontsize=12, fontweight='bold', 
                         color='darkgreen' if not self.game.game_over or self.game.game_won else 'darkred')

        # Status text with clear formatting
        status_text = "MISSION STATUS\n" + "="*25 + "\n\n"

        # Pictures remaining
        status_text += f"PICTURES: {self.game.pictures_remaining}/5 remaining\n"
        status_text += f"PICTURES USED: {self.game.pictures_taken}\n"
        
        # Movement statistics
        status_text += f"MOVES: {self.game.total_moves} | TURNS: {self.game.total_turns}\n\n"

        # Add animals status with clear presentation
        status_text += "PHOTO COLLECTION:\n"
        animals_info = [
            ('zebra', 'Z', 'ZEBRA'),
            ('elephant', 'E', 'ELEPHANT'), 
            ('oryx', 'O', 'ORYX')
        ]
        
        for animal, symbol, name in animals_info:
            photographed = self.game.animals_photographed[animal]
            if photographed:
                status_text += f"[{symbol}] {name}: CAPTURED!\n"
            else:
                status_text += f"[{symbol}] {name}: MISSING\n"
        
        # Progress bar
        total_animals = len(self.game.animals_photographed)
        captured = sum(self.game.animals_photographed.values())
        progress = "█" * captured + "░" * (total_animals - captured)
        status_text += f"\nProgress: [{progress}] {captured}/{total_animals}\n\n"
        
        # Controls section with styling
        status_text += "CONTROLS:\n" + "-"*15 + "\n"
        if self.game.game_over:
            # Show restart/quit options when game is over
            status_text += "Any action key: RESTART\n"
            status_text += "Q: QUIT GAME\n"
        else:
            # Show normal controls during gameplay
            status_text += "↑↓←→: MOVE DRONE\n"
            status_text += "A/D: TURN RIGHT/LEFT\n"
            status_text += "Enter: TAKE PHOTO\n"
            status_text += "R: RESET MISSION\n"
            status_text += "Q/ESC: QUIT\n"
        
        # Latest action result with clear presentation
        message = self.game.message
        if len(message) > 90:  # Increased from 60 to allow longer messages
            message = message[:87] + "..."
        
        status_text += "\n" + "="*25 + "\n"
        if self.game.game_over:
            if self.game.game_won:
                status_text += "MISSION COMPLETE!\n"
            else:
                status_text += "MISSION FAILED!\n"
        else:
            status_text += "LATEST ACTION:\n"
        status_text += f"> {message}"

        # Position status text with enhanced styling
        box_color = 'lightblue' if self.game.game_won else ('lightgreen' if not self.game.game_over else 'lightcoral')
        self.ax.text(1.02, 0.98, status_text, transform=self.ax.transAxes, 
                    fontsize=9, verticalalignment='top', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.6", facecolor=box_color, alpha=0.9, 
                             edgecolor='black', linewidth=2),
                    wrap=True)
        
        self.fig.canvas.draw()
    
    def start_interactive_game(self):
        """Start the interactive game with keyboard controls"""
        print("\n" + "🚁"*20)
        print("🎯 *** WELCOME TO DRONE SAFARI MISSION! *** 🎯")
        print("🚁"*20)
        print("🌍 MISSION BRIEFING:")
        print("📸 Photograph all wildlife without crashing!")
        print("🦓🐘🦌 Find and capture: Zebra, Elephant, Oryx")
        print("⚠️  Stay 2 cells away when taking photos")
        print("🎯 WARNING: You only have 5 pictures total!")
        print("📸 Wasted pictures count against your limit!")
        print("\n🎮 MISSION CONTROLS:")
        print("🚁 Arrow Keys: Move drone (↑=forward, ↓=back, ←=left, →=right)")
        print("🧭 A/D Keys: Turn right/left")
        print("📸 Enter Key: Take picture (LIMITED TO 5 TOTAL!)")
        print("🔄 R Key: Reset mission")
        print("🚪 Q/ESC Key: Abort mission")
        print("🔄 When mission ends: Any action key restarts, Q quits")
        print("="*60)
        print("🎯 MISSION OBJECTIVE: Photograph all three animals without crashing!")
        print("📏 Stay exactly 2 cells away when taking pictures.")
        print("🎮 Controls: Use arrow keys for movement and A/D for turning.")
        print("="*60)
        print("🚀 MISSION STATUS: READY TO DEPLOY!")
        
        # Create the matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(14, 10))
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # Initial display
        self.update_display()
        
        # Make sure the plot window can receive keyboard focus
        self.fig.canvas.manager.set_window_title("Drone Safari Game - Use keyboard to control!")
        
        print("Click on the game window and use your keyboard to play!")
        print("Close the window or press Q/ESC to quit.")
        
        # Show the plot and keep it interactive
        plt.show()


def main():
    """Main function to run the interactive game"""
    try:
        interactive_game = InteractiveDroneSafariGame()
        interactive_game.start_interactive_game()
    except KeyboardInterrupt:
        print("\nGame interrupted by user. Goodbye!")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure you have matplotlib installed and a display available.")


if __name__ == "__main__":
    main()
