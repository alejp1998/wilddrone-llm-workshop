"""
DRONE SAFARI GAME
================

PURPOSE:
This is an interactive drone navigation game where players must photograph wildlife 
while avoiding obstacles and managing limited resources.

OBJECTIVE:
Navigate a drone through a 12x12 grid to photograph all three animals (Zebra, Elephant, Oryx)
without crashing or scaring them away.

GAME RULES:
- Start at position (6,6) facing North
- You have only 5 pictures total (including wasted shots)
- Must stay exactly 2 cells away from animals when photographing
- Getting too close (adjacent) to animals scares them away = GAME OVER
- Crashing into trees, animals, or grid boundaries = GAME OVER
- Trees block your camera view when taking pictures

CONTROLS:
- Arrow Keys: Move drone (↑=forward, ↓=backward, ←=left, →=right)
- A/D Keys: Turn left/right (changes facing direction)
- Enter: Take picture (limited to 5 total!)
- R: Reset game
- Q/ESC: Quit game

GAME MODES:
1. Interactive Mode: Run main() for keyboard-controlled gameplay with live visualization
2. Programmatic Mode: Create DroneSafariGame() instance and call methods directly

KEY METHODS:
- move(direction, sensors=False): Move drone ('forward', 'backward', 'left', 'right')
- turn(direction, sensors=False): Turn drone ('left', 'right')  
- take_picture(sensors=False): Attempt to photograph (costs 1 of 5 pictures)
- get_status(): Get current game state
- visualize(): Display current game state
- reset_game(): Start over

SENSOR FUNCTIONALITY:
- Set sensors=True in move(), turn(), or take_picture() methods for environment scanning
- Sensors detect objects (trees, animals, boundaries) within 2 cells of drone position
- Provides directional information (north, south, east, west, etc.) and distances
- Helps with navigation and situational awareness during programmatic control

STRATEGY TIPS:
- Plan your route to minimize wasted pictures
- Use turns strategically to face animals from 2 cells away
- Watch out for trees blocking your camera view
- Remember: movement is relative to drone's facing direction

FAILURE CONDITIONS:
- Boundary crash: Flying outside the 12x12 grid
- Tree crash: Hitting a tree
- Scared animal: Getting adjacent to an animal
- Out of pictures: Using all 5 pictures without photographing all animals

WIN CONDITION:
Successfully photograph all three animals (Zebra, Elephant, Oryx) within 5 pictures
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import ListedColormap
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import os

# Game configuration
GRID_SIZE = 12
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

MOVE_TYPES = ['forward', 'left', 'right', 'backward']

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
        self.drone_pos = [6, 6]  # Start in middle of grid
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
        
        # Trail tracking for visualization
        self.movement_trail = []  # Track (prev_pos, new_pos) for movement lines
        self.rotation_trail = []  # Track (pos, prev_facing, new_facing) for rotation indicators
        
        self._setup_grid()
        
    def _setup_grid(self):
        """Initialize the grid with trees and animals"""
        # Add some trees randomly (adjusted for 12x12 grid)
        tree_positions = [
            (2, 3), (4, 8), (9, 5), (1, 10), (11, 2),
            (5, 1), (8, 9), (3, 6), (7, 11), (2, 9),
            (10, 4), (5, 3), (9, 8), (3, 4), (11, 6)
        ]
        
        for pos in tree_positions:
            if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                self.grid[pos] = TREE
        
        # Place animals in safe positions (not too close to trees or drone)
        animal_positions = {
            ZEBRA: (3, 3),
            ELEPHANT: (9, 9), 
            ORYX: (2, 9)
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
    
    def _get_absolute_direction(self, move_type):
        """Convert relative direction to absolute direction based on current facing"""
        facing_index = list(DIRECTIONS.keys()).index(self.drone_facing)

        if move_type == 'forward':
            return self.drone_facing
        elif move_type == 'backward':
            return list(DIRECTIONS.keys())[(facing_index + 2) % 4]
        elif move_type == 'right':
            return list(DIRECTIONS.keys())[(facing_index + 1) % 4]
        elif move_type == 'left':
            return list(DIRECTIONS.keys())[(facing_index - 1) % 4]
        
        return (0, 0)  # No movement
    
    def _get_sensor_summary(self):
        """Scan surrounding cells up to 2 cells away and return a summary of detected objects"""
        detections = []
        current_row, current_col = self.drone_pos
        
        # Object type names
        object_names = {
            TREE: "tree",
            ZEBRA: "zebra",
            ELEPHANT: "elephant", 
            ORYX: "oryx"
        }
        
        def format_direction(dr, dc):
            """Format direction as precise coordinates like '1 North 2 East'"""
            parts = []
            if dr < 0:  # North (negative row is north)
                parts.append(f"{abs(dr)} North")
            elif dr > 0:  # South (positive row is south)
                parts.append(f"{dr} South")
            
            if dc > 0:  # East (positive column is east)
                parts.append(f"{dc} East")
            elif dc < 0:  # West (negative column is west)
                parts.append(f"{abs(dc)} West")
            
            return " ".join(parts) if parts else "at current position"
        
        # Scan in a 5x5 grid centered on drone (2 cells in each direction)
        for distance in range(1, 3):  # 1 and 2 cells away
            for dr in range(-distance, distance + 1):
                for dc in range(-distance, distance + 1):
                    # Skip the center (drone position) and cells not exactly at current distance
                    if (dr == 0 and dc == 0) or (abs(dr) < distance and abs(dc) < distance):
                        continue
                    
                    scan_row = current_row + dr
                    scan_col = current_col + dc
                    
                    # Check if position is within grid bounds
                    if not self._is_valid_position(scan_row, scan_col):
                        # Check which boundary is being approached
                        boundary_desc = []
                        if scan_row < 0:
                            boundary_desc.append("north boundary")
                        elif scan_row >= GRID_SIZE:
                            boundary_desc.append("south boundary")
                        if scan_col < 0:
                            boundary_desc.append("west boundary")
                        elif scan_col >= GRID_SIZE:
                            boundary_desc.append("east boundary")
                        
                        if boundary_desc:
                            direction_str = format_direction(dr, dc)
                            detections.append(f"{' and '.join(boundary_desc)} at {direction_str}")
                        continue
                    
                    # Check what's at this position
                    cell_value = self.grid[scan_row, scan_col]
                    if cell_value in object_names:
                        direction_str = format_direction(dr, dc)
                        detections.append(f"{object_names[cell_value]} at {direction_str}")
                    
                    # Check for scared animals at this position
                    if (scan_row, scan_col) in self.scared_animals:
                        direction_str = format_direction(dr, dc)
                        detections.append(f"scared animal location at {direction_str}")
        
        if not detections:
            return "Sensors summary: Nothing of interest detected within 2 cells."
        else:
            return "Sensors summary: " + "; ".join(detections) + "."

    # Tool methods
    def move(self, move_type, sensors=False):
        """Move the drone with the specified move_type
        
        Args:
            move_type (str): Direction to move ('forward', 'backward', 'left', 'right')
            sensors (bool): If True, include sensor scan of surrounding area up to 2 cells away
            
        Returns:
            str: Result message, optionally including sensor summary if sensors=True
        """
        if self.game_over:
            return "Game is over! Reset to play again."
        
        if move_type not in MOVE_TYPES:
            return f"Invalid move_type: {move_type}. Use: {MOVE_TYPES}"

        # Get the movement delta
        absolute_dir = self._get_absolute_direction(move_type)
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
            result = self.message
            if sensors:
                result += "\n" + self._get_sensor_summary()
            return result
        
        # Check for collision with tree
        if self.grid[new_row, new_col] == TREE:
            self.drone_pos = [new_row, new_col]  # Update position to show crash location
            self.game_over = True
            self.failure_reason = "tree_crash"
            self.message = "Drone crashed into a tree!"
            result = self.message
            if sensors:
                result += "\n" + self._get_sensor_summary()
            return result
        
        # Check for collision with animal
        if self.grid[new_row, new_col] in [ZEBRA, ELEPHANT, ORYX]:
            self.drone_pos = [new_row, new_col]  # Update position to show crash location
            self.game_over = True
            self.failure_reason = "animal_crash"
            self.message = "Drone crashed into an animal!"
            result = self.message
            if sensors:
                result += "\n" + self._get_sensor_summary()
            return result
        
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
            result = self.message
            if sensors:
                result += "\n" + self._get_sensor_summary()
            return result
        
        # Move is valid
        # Add movement trail immediately (before moving to new position)
        self.movement_trail.append((self.drone_pos[:], [new_row, new_col]))
        
        # Update drone position
        self.drone_pos = [new_row, new_col]
        self.total_moves += 1  # Increment move counter
        self.message = f"Moved {move_type} to position ({new_row}, {new_col}), facing {self.drone_facing}"
        result = self.message
        if sensors:
            result += "\n" + self._get_sensor_summary()
        return result

    def turn(self, turn_direction, sensors=False):
        """Turn the drone left or right
        
        Args:
            turn_direction (str): Direction to turn ('left' or 'right')
            sensors (bool): If True, include sensor scan of surrounding area up to 2 cells away
            
        Returns:
            str: Result message, optionally including sensor summary if sensors=True
        """
        if self.game_over:
            return "Game is over! Reset to play again."

        if turn_direction not in ['left', 'right']:
            return "Invalid turn direction. Use 'left' or 'right'."
        
        facing_index = list(DIRECTIONS.keys()).index(self.drone_facing)

        if turn_direction == 'left':
            new_facing_index = (facing_index - 1) % 4
        else:  # right
            new_facing_index = (facing_index + 1) % 4

        # Store previous facing for trail BEFORE updating the facing direction
        old_facing = self.drone_facing
        
        # Update facing direction
        self.drone_facing = list(DIRECTIONS.keys())[new_facing_index]
        
        # Add rotation trail with old and new facing directions
        self.rotation_trail.append((self.drone_pos[:], old_facing, self.drone_facing))
        self.total_turns += 1  # Increment turn counter
        self.message = f"Turned {turn_direction}, now facing {self.drone_facing}"
        result = self.message
        if sensors:
            result += "\n" + self._get_sensor_summary()
        return result
    
    def take_picture(self, sensors=False):
        """Attempt to take a picture of an animal
        
        Args:
            sensors (bool): If True, include sensor scan of surrounding area up to 2 cells away
            
        Returns:
            str: Result message, optionally including sensor summary if sensors=True
        """
        if self.game_over:
            return "Game is over! Reset to play again."
        
        # Check if there are pictures remaining
        if self.pictures_remaining <= 0:
            self.message = "No pictures remaining! You've used all 5 pictures."
            self.game_over = True
            result = self.message
            if sensors:
                result += "\n" + self._get_sensor_summary()
            return result
        
        # Use one picture
        self.pictures_remaining -= 1
        self.pictures_taken += 1
        
        # Check if there's an animal exactly 2 cells away in the facing direction
        dr, dc = DIRECTIONS[self.drone_facing]
        target_row = self.drone_pos[0] + 2 * dr
        target_col = self.drone_pos[1] + 2 * dc
        
        # Check if there's a tree blocking the view (1 cell away from drone)
        blocking_row = self.drone_pos[0] + dr
        blocking_col = self.drone_pos[1] + dc
        
        # Check if target is out of bounds
        if not self._is_valid_position(target_row, target_col):
            # Record the photographed location for visualization (out of bounds shot)
            if self._is_valid_position(target_row, target_col):
                self.photographed_locations[(target_row, target_col)] = self.pictures_taken
            self.message = f"Picture #{self.pictures_taken} wasted! No animal in range to photograph. {self.pictures_remaining} pictures remaining."
            if self.pictures_remaining == 0:
                self.game_over = True
                self.message += " Game Over - No pictures left!"
            result = self.message
            if sensors:
                result += "\n" + self._get_sensor_summary()
            return result
        
        # Check if there's a tree blocking the view
        if (self._is_valid_position(blocking_row, blocking_col) and 
            self.grid[blocking_row, blocking_col] == TREE):
            # Record the photographed location as the blocking tree (where photo was actually taken)
            self.photographed_locations[(blocking_row, blocking_col)] = self.pictures_taken
            self.message = f"Picture #{self.pictures_taken} wasted! A tree is blocking your view. {self.pictures_remaining} pictures remaining."
            if self.pictures_remaining == 0:
                self.game_over = True
                self.failure_reason = "out_of_pictures"
                self.message += " Game Over - No pictures left and mission incomplete!"
            result = self.message
            if sensors:
                result += "\n" + self._get_sensor_summary()
            return result
        
        # Record the photographed location for visualization (normal case - target location)
        if self._is_valid_position(target_row, target_col):
            self.photographed_locations[(target_row, target_col)] = self.pictures_taken
        
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
        
        result = self.message
        if sensors:
            result += "\n" + self._get_sensor_summary()
        return result

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
    
    def get_grid_string(self):
        """Get a text representation of the current game grid"""
        # Create symbols for different elements
        symbols = {
            EMPTY: '.',
            TREE: 'T',
            ZEBRA: 'Z',
            ELEPHANT: 'E',
            ORYX: 'O'
        }
        
        # Direction symbols for drone
        direction_symbols = {
            'North': '^',
            'East': '>',
            'South': 'v',
            'West': '<'
        }
        
        grid_lines = []
        grid_lines.append("Grid Legend: D=Drone, T=Tree, Z=Zebra, E=Elephant, O=Oryx, .=Empty")
        grid_lines.append("   " + "".join([f"{i:2}" for i in range(min(10, GRID_SIZE))]))  # Column numbers
        
        for row in range(GRID_SIZE):
            line = f"{row:2} "  # Row number
            for col in range(GRID_SIZE):
                # Check if drone is at this position
                if [row, col] == self.drone_pos:
                    line += direction_symbols[self.drone_facing] + " "
                # Check if this location was scared (animal ran away)
                elif (row, col) in self.scared_animals:
                    line += "! "  # Scared animal marker
                # Check if this location was photographed
                elif (row, col) in self.photographed_locations:
                    line += "* "  # Photo taken marker
                else:
                    # Show grid element
                    element = self.grid[row, col]
                    line += symbols.get(element, '?') + " "
            grid_lines.append(line)
        
        return "\n".join(grid_lines)
    
    def reset_game(self):
        """Reset the game to initial state"""
        self.__init__()
        return "Game reset! Ready to start again."
    
    def visualize(self, figsize=(8, 6)):
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
        shining_icon = load_icon('shining.png', zoom=0.06)
        
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
        
        # Draw movement trail (dashed blue lines from previous positions)
        for prev_pos, curr_pos in self.movement_trail:
            prev_row, prev_col = prev_pos
            curr_row, curr_col = curr_pos
            ax.plot([prev_col, curr_col], [prev_row, curr_row], 
                   'b--', linewidth=2, alpha=0.7, zorder=9, label='Movement Trail' if len(self.movement_trail) == 1 else "")
        
        # Draw rotation indicators (improved visualization)
        for pos, prev_facing, new_facing in self.rotation_trail:
            rot_row, rot_col = pos
            
            # Calculate the direction vectors for previous and new facing
            prev_dr, prev_dc = DIRECTIONS[prev_facing]
            new_dr, new_dc = DIRECTIONS[new_facing]
            
            # Calculate points at the actual edge of the cell for clearer visualization
            edge_distance = 0.5  # Go to the actual edge of the cell
            
            # Start point: where drone was previously facing (edge of cell)
            start_row = rot_row + prev_dr * edge_distance
            start_col = rot_col + prev_dc * edge_distance
            
            # End point: where drone is now facing (edge of cell)
            end_row = rot_row + new_dr * edge_distance
            end_col = rot_col + new_dc * edge_distance
            
            # Create a curved path for the rotation using a simple arc
            # Calculate the midpoint with some offset to create the curve
            mid_row = rot_row
            mid_col = rot_col
            
            # Determine curve direction based on turn type
            prev_angle = list(DIRECTIONS.keys()).index(prev_facing) * 90
            new_angle = list(DIRECTIONS.keys()).index(new_facing) * 90
            angle_diff = (new_angle - prev_angle) % 360
            if angle_diff > 180:
                angle_diff -= 360
            
            # Generate curve points
            t = np.linspace(0, 1, 10)
            curve_factor = 0.15 if abs(angle_diff) == 90 else 0.25  # Less curve for 90° turns
            
            # Fix the curve direction - it should curve in the opposite direction
            if angle_diff > 0:  # Right turn - curve counterclockwise (opposite of before)
                offset_row = curve_factor * (end_col - start_col)
                offset_col = -curve_factor * (end_row - start_row)
            else:  # Left turn - curve clockwise (opposite of before)
                offset_row = -curve_factor * (end_col - start_col)
                offset_col = curve_factor * (end_row - start_row)
            
            # Calculate curved path points
            curve_rows = []
            curve_cols = []
            for ti in t:
                # Quadratic Bezier curve
                control_row = (start_row + end_row) / 2 + offset_row
                control_col = (start_col + end_col) / 2 + offset_col
                
                curve_row = (1-ti)**2 * start_row + 2*(1-ti)*ti * control_row + ti**2 * end_row
                curve_col = (1-ti)**2 * start_col + 2*(1-ti)*ti * control_col + ti**2 * end_col
                
                curve_rows.append(curve_row)
                curve_cols.append(curve_col)
            
            # Draw the curved path as dashed line
            ax.plot(curve_cols, curve_rows, 'r--', linewidth=2.5, alpha=0.8, zorder=9)
            
            # Add arrowhead at the end
            arrow_length = 0.1
            arrow_width = 0.08
            
            # Calculate arrow direction from the last two points
            if len(curve_rows) >= 2:
                dx = curve_cols[-1] - curve_cols[-2]
                dy = curve_rows[-1] - curve_rows[-2]
                length = np.sqrt(dx**2 + dy**2)
                if length > 0:
                    dx /= length
                    dy /= length
                    
                    # Draw arrowhead
                    ax.arrow(curve_cols[-2], curve_rows[-2], dx*arrow_length, dy*arrow_length,
                            head_width=arrow_width, head_length=arrow_length*0.6, 
                            fc='red', ec='red', linewidth=2, alpha=0.8, zorder=10)
            
            # Add a small rotation center marker
            center_circle = patches.Circle((rot_col, rot_row), 0.04, 
                                         facecolor='navy', 
                                         edgecolor='red', 
                                         linewidth=1, 
                                         zorder=11, 
                                         alpha=0.9)
            ax.add_patch(center_circle)
        
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
                    # Add facing direction indicator (blue arrow overlay)
                    dr, dc = DIRECTIONS[self.drone_facing]
                    ax.arrow(drone_col, drone_row, dc*0.7, dr*0.7, 
                            head_width=0.15, head_length=0.12, fc='blue', ec='blue', zorder=11, linewidth=2)
                else:
                    # Fallback: Draw normal drone in blue
                    circle = patches.Circle((drone_col, drone_row), 0.3, color='blue', zorder=10)
                    ax.add_patch(circle)
                    
                    # Draw facing direction arrow (blue)
                    dr, dc = DIRECTIONS[self.drone_facing]
                    ax.arrow(drone_col, drone_row, dc*0.7, dr*0.7, 
                            head_width=0.15, head_length=0.12, fc='blue', ec='blue', zorder=11, linewidth=2)
        
        # Draw photo markers for all photographed locations
        for (photo_row, photo_col), picture_num in self.photographed_locations.items():
            # Use shining icon instead of cross
            if shining_icon is not None:
                add_icon_to_plot(ax, photo_col, photo_row, shining_icon, zorder=12)
            else:
                # Fallback: Draw a golden/yellow star shape
                star_points = []
                star_size = 0.3
                for i in range(10):
                    angle = i * np.pi / 5
                    radius = star_size if i % 2 == 0 else star_size * 0.4
                    x = photo_col + radius * np.cos(angle - np.pi/2)
                    y = photo_row + radius * np.sin(angle - np.pi/2)
                    star_points.append((x, y))
                star = patches.Polygon(star_points, facecolor='gold', edgecolor='orange', 
                                     linewidth=2, zorder=12)
                ax.add_patch(star)
            
            # Add picture number in lower right corner of the cell
            ax.text(photo_col + 0.35, photo_row - 0.35, f'#{picture_num}', 
                   ha='center', va='center', fontsize=8, fontweight='bold', 
                   color='black', zorder=14)
        
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
        ax.set_ylabel('Row →', fontsize=12, fontweight='bold')

        # Dynamic title with comprehensive status information
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
            # Create comprehensive status for ongoing mission
            animals_found = sum(self.animals_photographed.values())
            animals_list = []
            for animal, found in self.animals_photographed.items():
                if found:
                    animals_list.append(f"{animal.upper()}✓")
                else:
                    animals_list.append(f"{animal.upper()}✗")
            
            title = f'DRONE SAFARI MISSION\n'
            title += f'Position: {self.drone_pos} | Facing: {self.drone_facing}\n'
            title += f'Pictures: {self.pictures_remaining}/5 | Animals: {animals_found}/3 ({", ".join(animals_list)})'
            title_color = 'darkblue'
        
        ax.set_title(title, fontsize=14, fontweight='bold', color=title_color)
        
        # Set axis ticks to show numbers every 2 units (0, 2, 4, 6, ...)
        ax.set_xticks(range(0, GRID_SIZE, 2))
        ax.set_yticks(range(0, GRID_SIZE, 2))
        
        # DO NOT RETURN FIGURE TO AVOID DUPLICATE PLOTS
        return fig
    

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
            result = self.game.move('forward')  # Forward
        elif event.key == 'down':
            result = self.game.move('backward')  # Back
        elif event.key == 'left':
            result = self.game.move('left')  # Left
        elif event.key == 'right':
            result = self.game.move('right')  # Right
        
        # A and D keys for turning
        elif event.key == 'a':
            result = self.game.turn('left')
        elif event.key == 'd':
            result = self.game.turn('right')

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
        shining_icon = load_icon('shining.png', zoom=0.05)
        
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
                                head_width=0.12, head_length=0.1, fc='blue', ec='blue', zorder=11, linewidth=2)
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
            # Add shining icon to indicate photographed location
            if shining_icon is not None:
                add_icon_to_plot(self.ax, photo_col, photo_row, shining_icon, zorder=12)
            else:
                # Fallback: yellow star
                self.ax.plot(photo_col, photo_row, '*', color='gold', markersize=20, zorder=12)
            
            # Add picture number in lower right corner of the cell
            self.ax.text(photo_col + 0.35, photo_row - 0.35, f'#{picture_num}', 
                        ha='center', va='center', fontsize=8, fontweight='bold', 
                        color='black', zorder=14)
        
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
        print("🚁 Arrow Keys: Move drone (↑=forward, ↓=backward, ←=left, →=right)")
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
