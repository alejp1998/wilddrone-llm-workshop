/**
 * Drone Safari — pure game logic (faithful JS port of drone_safari_game.py).
 * No DOM / Pixi dependencies: works in the browser and under node:test.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.DroneSafari = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // ---- Constants (identical to the Python original) ----
  var GRID_SIZE = 12;
  var EMPTY = 0;
  var TREE = 1;
  var ZEBRA = 2;
  var ELEPHANT = 3;
  var ORYX = 4;

  // North = +row, East = +col, South = -row, West = -col (row 0 at map bottom)
  var DIRECTIONS = {
    North: [1, 0],
    East: [0, 1],
    South: [-1, 0],
    West: [0, -1],
  };
  var FACING_ORDER = ["North", "East", "South", "West"];
  var MOVE_TYPES = ["forward", "left", "right", "backward"];

  var ANIMAL_NAMES = {};
  ANIMAL_NAMES[ZEBRA] = "zebra";
  ANIMAL_NAMES[ELEPHANT] = "elephant";
  ANIMAL_NAMES[ORYX] = "oryx";

  var ANIMAL_KEYS = { zebra: "zebra", elephant: "elephant", oryx: "oryx" };

  /** Map rows are printed row-11 (top) → row-0 (bottom); each row has 12 symbols. */
  function parseMap(ascii) {
    var symbolToValue = { ".": EMPTY, T: TREE, Z: ZEBRA, E: ELEPHANT, O: ORYX };
    var grid = [];
    for (var r = 0; r < GRID_SIZE; r++)
      grid.push(new Array(GRID_SIZE).fill(EMPTY));
    var lines = ascii.trim().split("\n");
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i].trim();
      if (!line || line.startsWith("Grid Legend")) continue;
      var parts = line.split(/\s+/);
      var rowNum = parseInt(parts[0], 10);
      if (isNaN(rowNum)) continue;
      for (var c = 0; c < GRID_SIZE && c < parts.length - 1; c++) {
        var sym = parts[c + 1];
        if (sym in symbolToValue) grid[rowNum][c] = symbolToValue[sym];
      }
    }
    return grid;
  }

  var MAP_DEFINITIONS = {
    easy: parseMap(
      [
        "Grid Legend: T=Tree, Z=Zebra, E=Elephant, O=Oryx, .=Empty",
        "11 . . . . . . . . . . . .",
        "10 . . . . . . . . . . . .",
        " 9 . . . . . . . . . E . .",
        " 8 . . . . . . . . . . . .",
        " 7 . . . . . . . . . . . .",
        " 6 . . . . . . . . . . . .",
        " 5 . . . . . . . . . . . .",
        " 4 . . . . . . . T . . . .",
        " 3 . . . Z . . . . . . . .",
        " 2 . . . . . . . . . O . .",
        " 1 . . . . . . . . . . . .",
        " 0 . . . . . . . . . . . .",
      ].join("\n"),
    ),
    medium: parseMap(
      [
        "Grid Legend: T=Tree, Z=Zebra, E=Elephant, O=Oryx, .=Empty",
        "11 . . . . . . T . . . . .",
        "10 . . . . . . . . . . . .",
        " 9 . . . . . T . . . E . .",
        " 8 . . . . . . . . . . . .",
        " 7 . . . . . . . . . . . T",
        " 6 . . . . . . . . . . . .",
        " 5 . T . . . . . . . . . .",
        " 4 . . . . . . . . T . . .",
        " 3 . . . Z . . T . . . . .",
        " 2 . . . . . . . . . O . .",
        " 1 . . . . . . . . . . . .",
        " 0 . . . . . . . . . . . .",
      ].join("\n"),
    ),
    hard: parseMap(
      [
        "Grid Legend: T=Tree, Z=Zebra, E=Elephant, O=Oryx, .=Empty",
        "11 . . T . . . T . . . . .",
        "10 . . . . T . . . . . . .",
        " 9 . . . . . T . . T E . .",
        " 8 . . . . . . . . . T . .",
        " 7 . . . . . . . . . . . T",
        " 6 . . . . . . . . . . . .",
        " 5 . T . T . . . . . . . .",
        " 4 . . . . . . . . T . . .",
        " 3 . . . Z T . T . . . . .",
        " 2 . . . T . . . . . O . .",
        " 1 . . . . . . . . . . T .",
        " 0 . . . . . . . . . . . .",
      ].join("\n"),
    ),
  };

  // ---- Core game class ----
  function DroneSafariGame(difficulty) {
    this.difficulty = difficulty || "medium";
    this.grid = [];
    this.drone_pos = [6, 6];
    this.drone_facing = "North";
    this.animals_photographed = { zebra: false, elephant: false, oryx: false };
    this.pictures_remaining = 5;
    this.pictures_taken = 0;
    this.total_moves = 0;
    this.total_turns = 0;
    this.photographed_locations = {};
    this.scared_animals = [];
    this.game_over = false;
    this.game_won = false;
    this.failure_reason = null;
    this.message =
      "Game started! Navigate carefully. You can take up to 5 pictures.";
    this._setup_grid();
  }

  DroneSafariGame.prototype._setup_grid = function () {
    if (!(this.difficulty in MAP_DEFINITIONS)) {
      this.difficulty = "medium";
    }
    this.grid = MAP_DEFINITIONS[this.difficulty].map(function (row) {
      return row.slice();
    });
  };

  DroneSafariGame.prototype._is_valid_position = function (row, col) {
    return row >= 0 && row < GRID_SIZE && col >= 0 && col < GRID_SIZE;
  };

  DroneSafariGame.prototype._is_adjacent_to_animal = function (row, col) {
    for (var dr = -1; dr <= 1; dr++) {
      for (var dc = -1; dc <= 1; dc++) {
        if (dr === 0 && dc === 0) continue;
        var rr = row + dr;
        var cc = col + dc;
        if (
          this._is_valid_position(rr, cc) &&
          (this.grid[rr][cc] === ZEBRA ||
            this.grid[rr][cc] === ELEPHANT ||
            this.grid[rr][cc] === ORYX)
        ) {
          return true;
        }
      }
    }
    return false;
  };

  DroneSafariGame.prototype._get_absolute_direction = function (move_type) {
    var idx = FACING_ORDER.indexOf(this.drone_facing);
    if (move_type === "forward") return this.drone_facing;
    if (move_type === "backward") return FACING_ORDER[(idx + 2) % 4];
    if (move_type === "right") return FACING_ORDER[(idx + 1) % 4];
    if (move_type === "left") return FACING_ORDER[(idx + 3) % 4];
    return null;
  };

  DroneSafariGame.prototype._get_sensor_summary = function () {
    var detections = [];
    var curRow = this.drone_pos[0];
    var curCol = this.drone_pos[1];

    function format_direction(dr, dc) {
      var ns = dr > 0 ? dr + "N" : dr < 0 ? Math.abs(dr) + "S" : "0N";
      var ew = dc > 0 ? dc + "E" : dc < 0 ? Math.abs(dc) + "W" : "0E";
      return "(" + ns + ", " + ew + ")";
    }

    // Always include animal GPS positions
    for (var r = 0; r < GRID_SIZE; r++) {
      for (var c = 0; c < GRID_SIZE; c++) {
        var v = this.grid[r][c];
        if (v === ZEBRA || v === ELEPHANT || v === ORYX) {
          var dr = r - curRow;
          var dc = c - curCol;
          if (dr !== 0 || dc !== 0) {
            detections.push(
              ANIMAL_NAMES[v] + " GPS at " + format_direction(dr, dc),
            );
          }
        }
      }
    }

    // Proximity scan (1-2 cells) for trees and boundaries
    for (var dist = 1; dist <= 2; dist++) {
      for (var dr2 = -dist; dr2 <= dist; dr2++) {
        for (var dc2 = -dist; dc2 <= dist; dc2++) {
          if (
            (dr2 === 0 && dc2 === 0) ||
            (Math.abs(dr2) < dist && Math.abs(dc2) < dist)
          )
            continue;
          var sr = curRow + dr2;
          var sc = curCol + dc2;
          if (!this._is_valid_position(sr, sc)) {
            var boundary = [];
            if (sr < 0) boundary.push("north boundary");
            else if (sr >= GRID_SIZE) boundary.push("south boundary");
            if (sc < 0) boundary.push("west boundary");
            else if (sc >= GRID_SIZE) boundary.push("east boundary");
            if (boundary.length) {
              detections.push(
                boundary.join(" and ") + " at " + format_direction(dr2, dc2),
              );
            }
            continue;
          }
          if (this.grid[sr][sc] === TREE) {
            detections.push("tree at " + format_direction(dr2, dc2));
          }
        }
      }
    }

    return detections.length
      ? "Sensors summary: " + detections.join("; ") + "."
      : "Sensors summary: No objects detected nearby.";
  };

  DroneSafariGame.prototype.move = function (move_type, sensors) {
    if (this.game_over) return "Game is over! Reset to play again.";
    if (MOVE_TYPES.indexOf(move_type) === -1) {
      return (
        "Invalid move_type: " + move_type + ". Use: " + MOVE_TYPES.join(", ")
      );
    }

    var absDir = this._get_absolute_direction(move_type);
    var delta = DIRECTIONS[absDir];
    var newRow = this.drone_pos[0] + delta[0];
    var newCol = this.drone_pos[1] + delta[1];

    var result;
    if (!this._is_valid_position(newRow, newCol)) {
      this.drone_pos = [newRow, newCol];
      this.game_over = true;
      this.failure_reason = "boundary_crash";
      this.message = "Drone crashed! Flew outside the grid boundaries.";
      result = this.message;
    } else if (this.grid[newRow][newCol] === TREE) {
      this.drone_pos = [newRow, newCol];
      this.game_over = true;
      this.failure_reason = "tree_crash";
      this.message = "Drone crashed into a tree!";
      result = this.message;
    } else if (
      this.grid[newRow][newCol] === ZEBRA ||
      this.grid[newRow][newCol] === ELEPHANT ||
      this.grid[newRow][newCol] === ORYX
    ) {
      this.drone_pos = [newRow, newCol];
      this.game_over = true;
      this.failure_reason = "animal_crash";
      this.message = "Drone crashed into an animal!";
      result = this.message;
    } else if (this._is_adjacent_to_animal(newRow, newCol)) {
      for (var dr = -1; dr <= 1; dr++) {
        for (var dc = -1; dc <= 1; dc++) {
          if (dr === 0 && dc === 0) continue;
          var rr = newRow + dr;
          var cc = newCol + dc;
          if (
            this._is_valid_position(rr, cc) &&
            (this.grid[rr][cc] === ZEBRA ||
              this.grid[rr][cc] === ELEPHANT ||
              this.grid[rr][cc] === ORYX)
          ) {
            this.scared_animals.push([rr, cc]);
            this.grid[rr][cc] = EMPTY;
          }
        }
      }
      this.drone_pos = [newRow, newCol];
      this.game_over = true;
      this.failure_reason = "scared_animal";
      this.message = "Drone got too close to an animal and scared it away!";
      result = this.message;
    } else {
      this.drone_pos = [newRow, newCol];
      this.total_moves += 1;
      this.message =
        "Moved " +
        move_type +
        " to position (" +
        newRow +
        ", " +
        newCol +
        "), facing " +
        this.drone_facing;
      result = this.message;
    }
    if (sensors) result += "\n" + this._get_sensor_summary();
    return result;
  };

  DroneSafariGame.prototype.turn = function (turn_direction, sensors) {
    if (this.game_over) return "Game is over! Reset to play again.";
    if (turn_direction !== "left" && turn_direction !== "right") {
      return "Invalid turn direction. Use 'left' or 'right'.";
    }
    var idx = FACING_ORDER.indexOf(this.drone_facing);
    var newIdx = turn_direction === "left" ? (idx + 3) % 4 : (idx + 1) % 4;
    this.drone_facing = FACING_ORDER[newIdx];
    this.total_turns += 1;
    this.message =
      "Turned " + turn_direction + ", now facing " + this.drone_facing;
    var result = this.message;
    if (sensors) result += "\n" + this._get_sensor_summary();
    return result;
  };

  DroneSafariGame.prototype.take_picture = function (sensors) {
    if (this.game_over) return "Game is over! Reset to play again.";
    if (this.pictures_remaining <= 0) {
      this.message = "No pictures remaining! You've used all 5 pictures.";
      this.game_over = true;
      return this.message;
    }

    this.pictures_remaining -= 1;
    this.pictures_taken += 1;

    var delta = DIRECTIONS[this.drone_facing];
    var targetRow = this.drone_pos[0] + 2 * delta[0];
    var targetCol = this.drone_pos[1] + 2 * delta[1];
    var blockRow = this.drone_pos[0] + delta[0];
    var blockCol = this.drone_pos[1] + delta[1];

    var result;
    if (!this._is_valid_position(targetRow, targetCol)) {
      this.message =
        "Picture #" +
        this.pictures_taken +
        " wasted! No animal in range to photograph. " +
        this.pictures_remaining +
        " pictures remaining.";
      if (this.pictures_remaining === 0) {
        this.game_over = true;
        this.message += " Game Over - No pictures left!";
      }
      result = this.message;
    } else if (
      this._is_valid_position(blockRow, blockCol) &&
      this.grid[blockRow][blockCol] === TREE
    ) {
      this.photographed_locations[[blockRow, blockCol]] = this.pictures_taken;
      this.message =
        "Picture #" +
        this.pictures_taken +
        " wasted! A tree is blocking your view. " +
        this.pictures_remaining +
        " pictures remaining.";
      if (this.pictures_remaining === 0) {
        this.game_over = true;
        this.failure_reason = "out_of_pictures";
        this.message += " Game Over - No pictures left and mission incomplete!";
      }
      result = this.message;
    } else {
      this.photographed_locations[[targetRow, targetCol]] = this.pictures_taken;
      var animalValue = this.grid[targetRow][targetCol];
      if (
        animalValue === ZEBRA ||
        animalValue === ELEPHANT ||
        animalValue === ORYX
      ) {
        var key = ANIMAL_NAMES[animalValue];
        if (this.animals_photographed[key]) {
          this.message =
            "Picture #" +
            this.pictures_taken +
            " wasted! " +
            key.charAt(0).toUpperCase() +
            key.slice(1) +
            " already photographed. " +
            this.pictures_remaining +
            " pictures remaining.";
        } else {
          this.animals_photographed[key] = true;
          this.message =
            "Picture #" +
            this.pictures_taken +
            ": Successfully photographed the " +
            key +
            "! " +
            this.pictures_remaining +
            " pictures remaining.";
        }
      } else if (animalValue === TREE) {
        this.message =
          "Picture #" +
          this.pictures_taken +
          " wasted! You photographed a tree. " +
          this.pictures_remaining +
          " pictures remaining.";
      } else {
        this.message =
          "Picture #" +
          this.pictures_taken +
          " wasted! No animal in range to photograph. " +
          this.pictures_remaining +
          " pictures remaining.";
      }

      if (
        this.animals_photographed.zebra &&
        this.animals_photographed.elephant &&
        this.animals_photographed.oryx
      ) {
        this.game_won = true;
        this.game_over = true;
        this.message +=
          " Congratulations! You've photographed all animals and won the game!";
      } else if (this.pictures_remaining === 0) {
        this.game_over = true;
        this.failure_reason = "out_of_pictures";
        this.message += " Game Over - No pictures left and mission incomplete!";
      }
      result = this.message;
    }

    if (sensors) result += "\n" + this._get_sensor_summary();
    return result;
  };

  DroneSafariGame.prototype.get_status = function () {
    return {
      position: this.drone_pos.slice(),
      facing: this.drone_facing,
      pictures_remaining: this.pictures_remaining,
      pictures_taken: this.pictures_taken,
      animals_photographed: Object.assign({}, this.animals_photographed),
      total_moves: this.total_moves,
      total_turns: this.total_turns,
      game_over: this.game_over,
      game_won: this.game_won,
      failure_reason: this.failure_reason,
    };
  };

  DroneSafariGame.prototype.reset_game = function () {
    this.grid = MAP_DEFINITIONS[this.difficulty].map(function (row) {
      return row.slice();
    });
    this.drone_pos = [6, 6];
    this.drone_facing = "North";
    this.animals_photographed = { zebra: false, elephant: false, oryx: false };
    this.pictures_remaining = 5;
    this.pictures_taken = 0;
    this.total_moves = 0;
    this.total_turns = 0;
    this.photographed_locations = {};
    this.scared_animals = [];
    this.game_over = false;
    this.game_won = false;
    this.failure_reason = null;
    this.message =
      "Game started! Navigate carefully. You can take up to 5 pictures.";
  };

  return {
    GRID_SIZE: GRID_SIZE,
    EMPTY: EMPTY,
    TREE: TREE,
    ZEBRA: ZEBRA,
    ELEPHANT: ELEPHANT,
    ORYX: ORYX,
    DIRECTIONS: DIRECTIONS,
    MOVE_TYPES: MOVE_TYPES,
    MAP_DEFINITIONS: MAP_DEFINITIONS,
    DroneSafariGame: DroneSafariGame,
  };
});
