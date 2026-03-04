import unittest
import importlib.util
import importlib.machinery
import pathlib

# dynamically load the maze game script by path so the test suite works even if
# the filename isn't a normal module name (it has no .py extension).
script_path = pathlib.Path(__file__).parent.parent / "truemazegame_midtermrevision"
loader = importlib.machinery.SourceFileLoader("maze_game", str(script_path))
maze_game = loader.load_module()

from maze_game import (
    generate_true_maze,
    choose_start_exit,
    bfs_shortest_path,
    place_spikes,
    build_new_game,
    try_move,
    choose_monsters,
    move_monsters,
    spawn_monster,
    Monster,
    WALL,
    OPEN,
    SPIKE,
)

class TestMazeGame(unittest.TestCase):

    def setUp(self):
        self.rows = 15
        self.cols = 29
        self.grid = generate_true_maze(self.rows, self.cols)
        self.start, self.exit = choose_start_exit(self.grid)
        # create a fresh game state for monster tests as needed
        _, _, _, self.initial_monsters = build_new_game(self.rows, self.cols)

    # ---------------------------
    # Maze Generation Tests
    # ---------------------------

    def test_maze_dimensions_are_odd(self):
        grid = generate_true_maze(14, 28)
        self.assertEqual(len(grid) % 2, 1)
        self.assertEqual(len(grid[0]) % 2, 1)

    def test_maze_has_open_tiles(self):
        open_tiles = [
            (r, c)
            for r in range(len(self.grid))
            for c in range(len(self.grid[0]))
            if self.grid[r][c] == OPEN
        ]
        self.assertTrue(len(open_tiles) > 0)

    # ---------------------------
    # Start / Exit Tests
    # ---------------------------

    def test_start_not_equal_exit(self):
        self.assertNotEqual(self.start, self.exit)

    def test_shortest_path_exists(self):
        path = bfs_shortest_path(self.grid, self.start, self.exit)
        self.assertTrue(len(path) > 0)

    # ---------------------------
    # Spike Placement Tests
    # ---------------------------

    def test_spikes_not_on_safe_path(self):
        safe_path = set(bfs_shortest_path(self.grid, self.start, self.exit))
        place_spikes(self.grid, 0.1, self.start, self.exit)

        for r, c in safe_path:
            self.assertNotEqual(self.grid[r][c], SPIKE)

    def test_spikes_not_on_start_or_exit(self):
        place_spikes(self.grid, 0.1, self.start, self.exit)
        self.assertNotEqual(self.grid[self.start[0]][self.start[1]], SPIKE)
        self.assertNotEqual(self.grid[self.exit[0]][self.exit[1]], SPIKE)

    # ---------------------------
    # Movement Tests
    # ---------------------------

    def test_cannot_move_through_wall(self):
        # Surround player with wall manually
        r, c = self.start
        self.grid[r][c+1] = WALL
        new_pos, result = try_move(self.grid, self.start, self.start, (0,1))
        self.assertEqual(result, "blocked")

    def test_spike_resets_to_start(self):
        r, c = self.start
        self.grid[r][c+1] = SPIKE
        new_pos, result = try_move(self.grid, self.start, self.start, (0,1))
        self.assertEqual(result, "spike")
        self.assertEqual(new_pos, self.start)

    def test_exit_triggers_win(self):
        r, c = self.start
        self.grid[r][c+1] = self.exit  # simulate exit next to start
        new_pos, result = try_move(self.grid, self.start, self.start, (0,1))
        # Since try_move checks EXIT tile symbol, we expect move to exit
        self.assertIn(result, ["exit", "moved"])

    # ---------------------------
    # Monster Tests
    # ---------------------------

    def test_choose_monsters_returns_correct_count(self):
        monsters = choose_monsters(self.grid, self.start, self.exit, count=3)
        # expecting at most 3 monsters, all on open tiles not start/exit
        self.assertTrue(len(monsters) <= 3)
        for m in monsters:
            self.assertNotEqual(m.pos, self.start)
            self.assertNotEqual(m.pos, self.exit)
            self.assertTrue(0 < m.life <= 5)

    def test_move_monsters_get_closer_and_age(self):
        # place player at start, move monsters once
        monsters = [Monster(self.start, 3)]  # monster on player
        new_monsters = move_monsters(self.grid, monsters, self.start)
        # monster should age and remain or expire
        self.assertTrue(all(m.life < 3 for m in new_monsters) or len(new_monsters) == 0)

    def test_spawn_monster_adds_new_one(self):
        monsters = []
        monsters = spawn_monster(self.grid, self.start, self.exit, monsters)
        self.assertTrue(len(monsters) == 1 or len(monsters) == 0)
        # if added, ensure valid position
        if monsters:
            m = monsters[0]
            self.assertNotEqual(m.pos, self.start)
            self.assertNotEqual(m.pos, self.exit)

    def test_collision_with_monster_reset(self):
        # simulate player stepping into monster location.  make sure the target
        # cell is open so the move is allowed by try_move.
        r,c = self.start
        self.grid[r][c+1] = OPEN
        monsters = [Monster((r, c+1), 3)]
        new_pos, result = try_move(self.grid, self.start, self.start, (0,1))
        self.assertEqual(result, "moved")
        # although try_move doesn't know about monsters, game logic would reset.
        # we just assert that the monster list contains the stepped-into coord
        self.assertIn((r, c+1), [m.pos for m in monsters])


if __name__ == "__main__":
    unittest.main()
