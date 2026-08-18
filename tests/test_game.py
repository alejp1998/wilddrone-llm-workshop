"""Unit tests for the DroneSafariGame engine (no API keys required)."""

import pytest

from drone_safari_game import (
    DIRECTIONS,
    ELEPHANT,
    EMPTY,
    GRID_SIZE,
    MAP_DEFINITIONS,
    ORYX,
    TREE,
    ZEBRA,
    DroneSafariGame,
)


@pytest.fixture
def game():
    return DroneSafariGame(difficulty="medium")


# ---------------------------------------------------------------------------
# Grid setup
# ---------------------------------------------------------------------------


def test_grid_size_and_drone_start(game):
    assert game.grid.shape == (GRID_SIZE, GRID_SIZE)
    assert game.drone_pos == [6, 6]
    assert game.drone_facing == "North"


def test_grid_contains_expected_entities(game):
    """The medium map must contain trees and all three animal species."""
    assert TREE in game.grid
    assert ZEBRA in game.grid
    assert ELEPHANT in game.grid
    assert ORYX in game.grid


def test_unknown_difficulty_falls_back_to_medium():
    g = DroneSafariGame(difficulty="impossible-mode")
    assert g.difficulty == "medium"


def test_all_difficulties_parse():
    for difficulty in MAP_DEFINITIONS:
        g = DroneSafariGame(difficulty=difficulty)
        assert g.grid.shape == (GRID_SIZE, GRID_SIZE)
        # At least one animal per difficulty
        assert any(
            g.grid[r, c] in (ZEBRA, ELEPHANT, ORYX)
            for r in range(GRID_SIZE)
            for c in range(GRID_SIZE)
        )


def test_initial_state_flags(game):
    assert game.game_over is False
    assert game.game_won is False
    assert game.pictures_remaining == 5
    assert game.pictures_taken == 0
    assert game.total_moves == 0
    assert game.total_turns == 0


# ---------------------------------------------------------------------------
# Movement
# ---------------------------------------------------------------------------


def test_move_forward_updates_position(game):
    # Facing North -> row increases (per DIRECTIONS mapping)
    dr, dc = DIRECTIONS["North"]
    start = game.drone_pos[:]
    msg = game.move("forward")
    assert game.drone_pos == [start[0] + dr, start[1] + dc]
    assert game.total_moves == 1
    assert "Moved forward" in msg


def test_move_backward_moves_opposite(game):
    game.turn("right")  # face East
    dr, dc = DIRECTIONS["East"]
    start = game.drone_pos[:]
    game.move("backward")
    assert game.drone_pos == [start[0] - dr, start[1] - dc]


def test_move_left_and_right_are_relative(game):
    game.turn("left")  # face West
    game.turn("right")  # back to North
    assert game.drone_facing == "North"


def test_invalid_move_type_rejected(game):
    msg = game.move("teleport")
    assert "Invalid move_type" in msg
    assert game.drone_pos == [6, 6]


def test_boundary_crash(game):
    # Clear the column so nothing blocks the drone, then fly North out of bounds
    for r in range(GRID_SIZE):
        game.grid[r, 6] = EMPTY
    for _ in range(GRID_SIZE):  # 12 moves is enough to exit a 12x12 grid from row 6
        game.move("forward")
    assert game.game_over is True
    assert game.failure_reason == "boundary_crash"


def test_tree_crash(game):
    # Find a tree cell and place the drone adjacent, facing it
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if game.grid[r, c] == TREE:
                # Try to approach from the south (row-1 facing North)
                if r > 0 and game.grid[r - 1, c] == EMPTY:
                    game.drone_pos = [r - 1, c]
                    game.drone_facing = "North"
                    msg = game.move("forward")
                    assert game.failure_reason == "tree_crash"
                    assert "tree" in msg
                    return
    pytest.fail("No approachable tree found in medium map")


def test_move_after_game_over_blocked(game):
    game.game_over = True
    msg = game.move("forward")
    assert "Game is over" in msg


# ---------------------------------------------------------------------------
# Turns
# ---------------------------------------------------------------------------


def test_turn_cycles_correctly(game):
    order = ["North", "East", "South", "West"]
    for expected in order[1:]:
        game.turn("right")
        assert game.drone_facing == expected
    game.turn("right")
    assert game.drone_facing == "North"


def test_turn_left_and_right_are_inverse(game):
    game.turn("right")
    game.turn("left")
    assert game.drone_facing == "North"
    assert game.total_turns == 2


def test_invalid_turn_rejected(game):
    msg = game.turn("up")
    assert "Invalid turn direction" in msg
    assert game.total_turns == 0


# ---------------------------------------------------------------------------
# Pictures
# ---------------------------------------------------------------------------


def test_picture_consumes_slot(game):
    msg = game.take_picture()
    assert game.pictures_taken == 1
    assert game.pictures_remaining == 4
    assert "wasted" in msg  # nothing in range from start


def test_no_pictures_left_ends_game(game):
    game.pictures_remaining = 0
    msg = game.take_picture()
    assert game.game_over is True
    assert "No pictures remaining" in msg


def test_win_when_all_animals_photographed(game):
    # Directly mark all animals photographed and verify win condition path
    game.animals_photographed = {"zebra": True, "elephant": True, "oryx": False}
    # Force a successful oryx shot: put oryx exactly 2 cells North with clear view
    r, c = game.drone_pos
    game.grid[r + 2, c] = ORYX
    game.grid[r + 1, c] = EMPTY
    game.drone_facing = "North"
    game.take_picture()
    assert game.game_won is True
    assert game.game_over is True
    assert "won" in game.message


def test_tree_blocks_photo(game):
    r, c = game.drone_pos
    game.grid[r + 1, c] = TREE
    game.grid[r + 2, c] = ZEBRA
    game.drone_facing = "North"
    game.take_picture()
    assert "tree is blocking" in game.message
    assert game.animals_photographed["zebra"] is False


def test_successful_photo_updates_state(game):
    r, c = game.drone_pos
    game.grid[r + 2, c] = ZEBRA
    game.grid[r + 1, c] = EMPTY
    game.drone_facing = "North"
    msg = game.take_picture()
    assert game.animals_photographed["zebra"] is True
    assert "Successfully photographed the zebra" in msg


# ---------------------------------------------------------------------------
# Animals & sensors
# ---------------------------------------------------------------------------


def test_adjacent_animal_scares_it_away(game):
    r, c = game.drone_pos
    # Place zebra TWO cells North: moving forward lands adjacent to it (not on it)
    game.grid[r + 1, c] = EMPTY
    game.grid[r + 2, c] = ZEBRA
    game.drone_facing = "North"
    game.move("forward")
    assert game.failure_reason == "scared_animal"
    assert game.game_over is True
    assert game.grid[r + 2, c] == EMPTY  # animal ran away
    assert (r + 2, c) in game.scared_animals


def test_animal_crash(game):
    r, c = game.drone_pos
    game.grid[r + 1, c] = ELEPHANT
    game.drone_facing = "North"
    game.move("forward")
    assert game.failure_reason == "animal_crash"


def test_sensor_summary_includes_animal_gps(game):
    summary = game._get_sensor_summary()
    assert "Sensors summary:" in summary
    assert "GPS" in summary


def test_sensors_flag_appends_summary(game):
    msg = game.move("forward", sensors=True)
    assert "Sensors summary:" in msg


# ---------------------------------------------------------------------------
# Reset & status
# ---------------------------------------------------------------------------


def test_reset_game_restores_state(game):
    game.move("forward")
    game.turn("right")
    game.take_picture()
    game.reset_game()
    assert game.drone_pos == [6, 6]
    assert game.drone_facing == "North"
    assert game.pictures_remaining == 5
    assert game.pictures_taken == 0
    assert game.total_moves == 0
    assert game.game_over is False
    assert game.game_won is False


def test_get_status_reports_key_state(game):
    status = game.get_status()
    assert isinstance(status, dict)
    assert "position" in status or "drone_position" in status
    assert "facing" in status
    assert status["facing"] == "North"
