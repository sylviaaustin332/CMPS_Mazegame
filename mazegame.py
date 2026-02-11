"""
Maze Game (Midterm Checkpoint 1)

This program generates and runs a terminal-based maze game.

High-level flow:
1. A maze is generated using recursive backtracking.
2. A start (S) and exit (E) are selected far apart.
3. Spikes (^) are placed randomly, but never on the guaranteed safe path.
4. The player (@) moves through the maze.
5. The game tracks steps and ends when the player reaches E.

The maze is always winnable because spikes are never placed on the
shortest path between start and exit.
"""


import os
import sys
import random
import time
from typing import List, Tuple, Optional

# TILE CONSTANTS
# These define how each tile type is displayed in the maze.

WALL = "#"
OPEN = " "      # open paths are blank
SPIKE = "^"
START = "S"
EXIT = "E"
PLAYER = "@"

# MOVEMENT MAP
# Maps keyboard input to row/column movement.
# (row change, column change)

MOVE_MAP = {
    "w": (-1, 0),
    "s": (1, 0),
    "a": (0, -1),
    "d": (0, 1),
    "q": (-1, -1),
    "e": (-1, 1),
    "z": (1, -1),
    "c": (1, 1),
}


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def read_char() -> str:
    """Single-character input (Windows + macOS/Linux)."""
    try:
        import msvcrt  # type: ignore

        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):
            msvcrt.getch()
            return ""
        try:
            return ch.decode("utf-8").lower()
        except Exception:
            return ""
    except ImportError:
        import tty
        import termios

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def in_bounds(grid: List[List[str]], r: int, c: int) -> bool:
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])


def render(grid: List[List[str]], player_pos: Tuple[int, int], steps: int) -> None:
    clear_screen()
    print("TRUE MAZE GAME")
    print("Controls: w/a/s/d, q/e/z/c (diagonals), r (restart), n (new maze), x (quit)")
    print(f"Steps: {steps}\n")

    pr, pc = player_pos
    for r, row in enumerate(grid):
        line = []
        for c, ch in enumerate(row):
            if (r, c) == (pr, pc):
                line.append(PLAYER)
            else:
                line.append(ch)
        print("".join(line))
    print()

# MAZE GENERATION
# Uses recursive backtracking to carve corridors.
# Starts with all walls and removes walls between cells.
# This guarantees all open spaces are connected.

def generate_true_maze(rows: int, cols: int, seed: Optional[int] = None) -> List[List[str]]:
    """Recursive backtracking "true maze" generator."""
    if seed is not None:
        random.seed(seed)

    if rows % 2 == 0:
        rows += 1
    if cols % 2 == 0:
        cols += 1

    grid = [[WALL for _ in range(cols)] for _ in range(rows)]
    carve_dirs = [(-2, 0), (2, 0), (0, -2), (0, 2)]

    def carve_from(r: int, c: int) -> None:
        grid[r][c] = OPEN
        random.shuffle(carve_dirs)
        for dr, dc in carve_dirs:
            nr, nc = r + dr, c + dc
            if not in_bounds(grid, nr, nc):
                continue
            if grid[nr][nc] == OPEN:
                continue

            wall_r, wall_c = r + dr // 2, c + dc // 2
            grid[wall_r][wall_c] = OPEN
            carve_from(nr, nc)

    start_r = random.randrange(1, rows, 2)
    start_c = random.randrange(1, cols, 2)
    carve_from(start_r, start_c)
    return grid

# BFS (Breadth-First Search)
# Used to find the farthest reachable open tile.
# This helps ensure the exit is placed far from the start.

def bfs_farthest_open(grid: List[List[str]], start: Tuple[int, int]) -> Tuple[int, int]:
    """BFS (4-dir) to find farthest open tile from start."""
    from collections import deque

    dirs4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    q = deque([start])
    dist = {start: 0}
    farthest = start

    while q:
        r, c = q.popleft()
        if dist[(r, c)] > dist[farthest]:
            farthest = (r, c)

        for dr, dc in dirs4:
            nr, nc = r + dr, c + dc
            if not in_bounds(grid, nr, nc):
                continue
            if grid[nr][nc] != OPEN:
                continue
            if (nr, nc) in dist:
                continue
            dist[(nr, nc)] = dist[(r, c)] + 1
            q.append((nr, nc))

    return farthest

# START & EXIT SELECTION
# Picks a random open tile as the start.
# Uses BFS to place the exit as far away as possible.

def choose_start_exit(grid: List[List[str]]) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Pick a random open tile as start; choose exit as farthest reachable open tile."""
    opens = [(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] == OPEN]
    if not opens:
        raise ValueError("No open tiles found in maze.")

    start = random.choice(opens)
    exit_pos = bfs_farthest_open(grid, start)
    return start, exit_pos

# SHORTEST PATH CALCULATION
# Uses BFS to compute the shortest path from start to exit.
# This path is protected from spike placement to guarantee
# the maze is always winnable.

def bfs_shortest_path(grid: List[List[str]], start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Shortest path (4-dir BFS) from start to goal."""
    from collections import deque

    dirs4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    q = deque([start])
    parent = {start: None}

    while q:
        r, c = q.popleft()
        if (r, c) == goal:
            break

        for dr, dc in dirs4:
            nr, nc = r + dr, c + dc
            if not in_bounds(grid, nr, nc):
                continue
            if grid[nr][nc] == WALL:
                continue
            if (nr, nc) in parent:
                continue
            parent[(nr, nc)] = (r, c)
            q.append((nr, nc))

    if goal not in parent:
        return []

    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path

# SPIKE PLACEMENT
# Randomly places spike tiles on open paths.
# Spikes are NEVER placed on the guaranteed safe path.

def place_spikes(grid: List[List[str]], spike_fraction: float, start_pos: Tuple[int, int], exit_pos: Tuple[int, int]) -> None:
    """Place spikes on OPEN tiles, but never on the safe BFS path from start to exit (always winnable)."""
    safe_path = set(bfs_shortest_path(grid, start_pos, exit_pos))

    open_tiles = [
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == OPEN and (r, c) not in safe_path and (r, c) not in (start_pos, exit_pos)
    ]

    spike_count = int(len(open_tiles) * spike_fraction)
    spike_count = max(0, min(spike_count, len(open_tiles)))

    for (r, c) in random.sample(open_tiles, spike_count):
        grid[r][c] = SPIKE

# GAME INITIALIZATION
# Generates maze, selects start and exit,
# places spikes, and prepares a new game state.

def build_new_game(rows: int = 15, cols: int = 29, spike_fraction: float = 0.06, seed: Optional[int] = None):
    grid = generate_true_maze(rows, cols, seed=seed)
    start_pos, exit_pos = choose_start_exit(grid)

    # place spikes while corridors are OPEN
    place_spikes(grid, spike_fraction, start_pos, exit_pos)

    # mark start/exit
    grid[start_pos[0]][start_pos[1]] = START
    grid[exit_pos[0]][exit_pos[1]] = EXIT

    return grid, start_pos, exit_pos

# PLAYER MOVEMENT LOGIC
# Attempts to move the player.
# Returns:
#   "blocked" if wall
#   "spike" if trap
#   "exit" if reached goal
#   "moved" if valid move

def try_move(grid: List[List[str]], player_pos: Tuple[int, int], start_pos: Tuple[int, int], delta: Tuple[int, int]):
    r, c = player_pos
    dr, dc = delta
    nr, nc = r + dr, c + dc

    if not in_bounds(grid, nr, nc):
        return player_pos, "blocked"

    target = grid[nr][nc]
    if target == WALL:
        return player_pos, "blocked"
    if target == SPIKE:
        return start_pos, "spike"
    if target == EXIT:
        return (nr, nc), "exit"
    return (nr, nc), "moved"  # OPEN or START

# MAIN GAME LOOP
# Continuously:
# - Renders the maze
# - Reads player input
# - Updates position
# - Checks win condition

def main() -> None:
    rows = 15
    cols = 29
    spike_fraction = 0.06
    seed = None

    grid, start_pos, exit_pos = build_new_game(rows, cols, spike_fraction, seed)
    player_pos = start_pos
    steps = 0

    while True:
        render(grid, player_pos, steps)

        if player_pos == exit_pos:
            print(f"🎉 You reached the exit in {steps} steps!")
            break

        print("Move: ", end="", flush=True)
        key = read_char().strip().lower()
        if key:
            print(key)

        if key == "x":
            print("Goodbye!")
            break
        if key == "r":
            player_pos = start_pos
            steps = 0
            continue
        if key == "n":
            grid, start_pos, exit_pos = build_new_game(rows, cols, spike_fraction, seed=None)
            player_pos = start_pos
            steps = 0
            continue
        if key not in MOVE_MAP:
            continue

        new_pos, result = try_move(grid, player_pos, start_pos, MOVE_MAP[key])

        if result == "blocked":
            continue

        player_pos = new_pos
        steps += 1

        if result == "spike":
            render(grid, player_pos, steps)
            print("💥 You stepped on a spike! Returning to start...")
            time.sleep(0.8)


if __name__ == "__main__":
    main()
