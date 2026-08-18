/**
 * Node test suite for the Drone Safari web game core.
 * Runs with: node --test webgame/tests/game-core.test.js
 */
const { test } = require("node:test");
const assert = require("node:assert");

const {
  GRID_SIZE,
  EMPTY,
  TREE,
  ZEBRA,
  ELEPHANT,
  ORYX,
  MAP_DEFINITIONS,
  DroneSafariGame,
} = require("../js/game-core.js");

function newGame(difficulty) {
  return new DroneSafariGame(difficulty || "medium");
}

// ---------------------------------------------------------------------------
// Grid setup (parity with the Python engine)
// ---------------------------------------------------------------------------

test("grid is 12x12 and drone starts at [6,6] facing North", () => {
  const g = newGame();
  assert.strictEqual(g.grid.length, GRID_SIZE);
  assert.strictEqual(g.grid[0].length, GRID_SIZE);
  assert.deepStrictEqual(g.drone_pos, [6, 6]);
  assert.strictEqual(g.drone_facing, "North");
});

test("all difficulty maps contain trees and the three animals", () => {
  for (const d of ["easy", "medium", "hard"]) {
    const g = newGame(d);
    const flat = g.grid.flat();
    assert.ok(flat.includes(TREE), d + " has trees");
    assert.ok(flat.includes(ZEBRA), d + " has zebra");
    assert.ok(flat.includes(ELEPHANT), d + " has elephant");
    assert.ok(flat.includes(ORYX), d + " has oryx");
  }
});

test("unknown difficulty falls back to medium", () => {
  const g = newGame("impossible");
  assert.strictEqual(g.difficulty, "medium");
});

test("map parity with Python: known entity positions", () => {
  // Medium map: zebra at row 3 col 3, elephant row 9 col 9, oryx row 2 col 9
  const g = newGame("medium");
  assert.strictEqual(g.grid[3][3], ZEBRA);
  assert.strictEqual(g.grid[9][9], ELEPHANT);
  assert.strictEqual(g.grid[2][9], ORYX);
  // Medium map: tree at row 11 col 6 and row 5 col 1
  assert.strictEqual(g.grid[11][6], TREE);
  assert.strictEqual(g.grid[5][1], TREE);
});

// ---------------------------------------------------------------------------
// Movement
// ---------------------------------------------------------------------------

test("moving forward 5 times from start is safe on medium", () => {
  const g = newGame("medium");
  // From (6,6) North: (7,6),(8,6),(9,6),(10,6),(11,6)=tree? row 11 col 6 is a tree!
  // So stop at 4 moves.
  for (let i = 0; i < 4; i++) g.move("forward");
  assert.deepStrictEqual(g.drone_pos, [10, 6]);
  assert.strictEqual(g.total_moves, 4);
  assert.strictEqual(g.game_over, false);
});

test("flying into a tree crashes the drone", () => {
  const g = newGame("medium");
  for (let i = 0; i < 5; i++) g.move("forward"); // (11,6) is TREE
  assert.strictEqual(g.game_over, true);
  assert.strictEqual(g.failure_reason, "tree_crash");
});

test("turn cycles North->East->South->West", () => {
  const g = newGame();
  g.turn("right");
  assert.strictEqual(g.drone_facing, "East");
  g.turn("right");
  assert.strictEqual(g.drone_facing, "South");
  g.turn("right");
  assert.strictEqual(g.drone_facing, "West");
  g.turn("right");
  assert.strictEqual(g.drone_facing, "North");
});

test("left then right returns to original facing", () => {
  const g = newGame();
  g.turn("left");
  const afterLeft = g.drone_facing;
  g.turn("right");
  assert.strictEqual(g.drone_facing, "North");
  assert.notStrictEqual(afterLeft, "North");
});

test("invalid move and turn are rejected", () => {
  const g = newGame();
  assert.match(g.move("teleport"), /Invalid move_type/);
  assert.deepStrictEqual(g.drone_pos, [6, 6]);
  assert.match(g.turn("up"), /Invalid turn direction/);
  assert.strictEqual(g.total_turns, 0);
});

test("moves after game over are blocked", () => {
  const g = newGame();
  g.game_over = true;
  assert.match(g.move("forward"), /Game is over/);
  assert.match(g.turn("left"), /Game is over/);
  assert.match(g.take_picture(), /Game is over/);
});

// ---------------------------------------------------------------------------
// Animals
// ---------------------------------------------------------------------------

test("moving adjacent to an animal scares it away", () => {
  const g = newGame();
  // Zebra two cells North of start (8,6)? Place it manually at (8,6), clear (7,6)
  g.grid[8][6] = ZEBRA;
  g.grid[7][6] = EMPTY;
  g.move("forward"); // land at (7,6), adjacent to (8,6)
  assert.strictEqual(g.failure_reason, "scared_animal");
  assert.strictEqual(g.grid[8][6], EMPTY); // ran away
  assert.strictEqual(g.scared_animals.length, 1);
});

test("moving onto an animal crashes the drone", () => {
  const g = newGame();
  g.grid[7][6] = ELEPHANT;
  g.move("forward");
  assert.strictEqual(g.failure_reason, "animal_crash");
});

test("sensor summary includes animal GPS positions", () => {
  const g = newGame("medium");
  const s = g._get_sensor_summary();
  assert.match(s, /Sensors summary:/);
  assert.match(s, /zebra GPS/);
  assert.match(s, /elephant GPS/);
});

// ---------------------------------------------------------------------------
// Pictures
// ---------------------------------------------------------------------------

test("successful zebra photo at exactly 2 cells", () => {
  const g = newGame();
  g.grid[8][6] = ZEBRA;
  g.grid[7][6] = EMPTY;
  g.take_picture();
  assert.strictEqual(g.animals_photographed.zebra, true);
  assert.strictEqual(g.pictures_remaining, 4);
});

test("tree between drone and animal blocks the photo", () => {
  const g = newGame();
  g.grid[7][6] = TREE;
  g.grid[8][6] = ZEBRA;
  const msg = g.take_picture();
  assert.match(msg, /tree is blocking/);
  assert.strictEqual(g.animals_photographed.zebra, false);
});

test("no animal in range wastes a picture", () => {
  const g = newGame();
  const msg = g.take_picture();
  assert.match(msg, /wasted/);
  assert.strictEqual(g.pictures_taken, 1);
  assert.strictEqual(g.pictures_remaining, 4);
});

test("photographing all three animals wins the game", () => {
  const g = newGame();
  g.animals_photographed = { zebra: true, elephant: true, oryx: false };
  // Oryx 2 cells North with clear view
  g.grid[8][6] = ORYX;
  g.grid[7][6] = EMPTY;
  g.take_picture();
  assert.strictEqual(g.game_won, true);
  assert.strictEqual(g.game_over, true);
  assert.match(g.message, /won/);
});

test("out of pictures ends the game", () => {
  const g = newGame();
  g.pictures_remaining = 0;
  const msg = g.take_picture();
  assert.strictEqual(g.game_over, true);
  assert.match(msg, /No pictures remaining/);
});

// ---------------------------------------------------------------------------
// Reset / status
// ---------------------------------------------------------------------------

test("reset restores the initial state", () => {
  const g = newGame("medium");
  g.move("forward");
  g.turn("right");
  g.take_picture();
  g.reset_game();
  assert.deepStrictEqual(g.drone_pos, [6, 6]);
  assert.strictEqual(g.drone_facing, "North");
  assert.strictEqual(g.pictures_remaining, 5);
  assert.strictEqual(g.total_moves, 0);
  assert.strictEqual(g.game_over, false);
});

test("status reports structured state", () => {
  const g = newGame();
  const s = g.get_status();
  assert.strictEqual(s.facing, "North");
  assert.deepStrictEqual(s.position, [6, 6]);
  assert.strictEqual(s.pictures_remaining, 5);
});
