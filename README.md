# True Maze Game

This is a terminal-based maze exploration game written in Python.  The goal is
to navigate from a random start (`SS`) to the exit (`EE`) while avoiding
spikes, walls, and transient monsters.

## Features

- **True maze generation** using recursive backtracking (perfect maze).
- Double-width Unicode tiles and ANSI color support for clean rendering.
- Diagonal movement with corner-cut prevention.
- Spikes placed off the safe path.
- Dynamic monsters (`👾`) that appear along the solution path, move toward the
  player, and vanish after a few turns.  New monsters may spawn every few
  moves.
- Controls: `w`/`a`/`s`/`d` for cardinal moves, `q`/`e`/`z`/`c` for diagonals.
  `r` restarts, `n` creates a new maze, `x` quits.

## Running

Simply execute the script with Python:

```bash
python truemazegame_midtermrevision
```

Ensure your terminal supports ANSI escape codes and the monster emoji.

## Code Organization

The entire gameplay logic lives in a single Python script.  To make the code
readable, each helper and game component is factored into its own function,
with descriptive docstrings explaining its behavior.  Below are expanded
summaries of the most important routines (see the file comments for even more
detail):

### Maze and topology helpers

- **`generate_true_maze(rows, cols, seed=None)`** – Constructs a perfect maze
  grid using recursive backtracking.  The function ensures odd dimensions and
  carves corridors by visiting cells in a randomized order.  An optional seed
  argument yields deterministic mazes for testing.

- **`bfs_farthest_open(grid, start)`** – Performs a breadth-first search from a
  start cell and returns the open cell at maximal distance.  Used by
  `choose_start_exit` to guarantee the exit is in the opposite corner of the
  maze.

- **`bfs_shortest_path(grid, start, goal)`** – Computes the shortest route
  between two open cells using BFS.  The returned list of coordinates serves
  multiple purposes: identifying the safe path for spike placement and
  determining monster spawn locations.

- **`choose_start_exit(grid)`** – Randomly picks a starting position from all
  open spaces, then finds the farthest reachable cell to serve as the exit.
  The start and exit are later marked on the grid with `SS` and `EE`.

### Obstacles and hazards

- **`place_spikes(grid, fraction, start, exit_pos)`** – Inserts spike tiles into
  the maze.  Spikes are only placed on open cells that are not part of the
  shortest path from start to exit, nor adjacent to the start.  The
  `fraction` parameter scales the total number of spikes.

- **`choose_monsters(grid, start, exit_pos, count=2)`** – Selects initial
  monster positions roughly evenly spaced along the safe path.  Each monster
  is assigned a random lifetime between three and five turns and represented by
  a named tuple.  This keeps hazards temporary and prevents clustering.

- **`move_monsters(grid, monsters, player)`** – Advances every monster one step
  closer to the player's current position, avoiding walls, spikes, start,
  exit, and collisions with other monsters.  Lives are decremented and expired
  monsters are removed.

- **`spawn_monster(grid, start, exit_pos, monsters)`** – Occasionally called
  during the game loop to add a fresh monster in a random free cell along the
  player's optimal path (excluding start/exit and occupied cells).  The new
  entity receives its own life counter.

### Player interaction

- **`try_move(grid, player, start, delta)`** – Handles player movement logic.
  The function tests for boundary conditions, wall collisions, diagonal corner
  cutting, and tile-specific effects (spike, exit).  It returns the new
  position along with a status string used by the loop.

- **`render(grid, player_pos, steps, monsters=None)`** – Clears the terminal and
  draws the maze row by row, coloring each tile type appropriately.  The
  player and any active monsters appear on top of the grid.  The step counter
  and controls are displayed at the top.

### Initialization and main loop

- **`build_new_game(rows=15, cols=29, spike_fraction=0.07, monster_count=None)`**
  – Orchestrates maze generation, start/exit selection, spike placement, and
  initial monster creation.  Returns the full game state (grid, start,
  exit_pos, monsters) ready for play.

- **`main()`** – Implements the core game loop: rendering, reading keystrokes,
  processing commands (`r`/`n`/`x`), moving the player, applying collisions,
  advancing and spawning monsters, and resetting the player on hazards.  The
  loop continues until the player reaches the exit or quits.

Docstrings are still the authoritative reference, but this section provides a
story-like walkthrough of how the pieces fit together.

## Extending the Game

The design is modular; you can tweak parameters such as maze size,
`spike_fraction`, monster spawn interval, or lifetime ranges.  Adding new
hazards or power-ups would involve extending `try_move` and the render logic.

Enjoy navigating the maze!
