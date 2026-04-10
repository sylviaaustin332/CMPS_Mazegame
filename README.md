True Maze Game

Sylvia Austin, Shayna Shpits, Lucy Pauze

This is a terminal-based maze exploration game written in Python. The goal is to navigate from a random start (SS) to the exit (EE) while avoiding spikes, walls, and transient monsters.

Features
True maze generation using recursive backtracking (perfect maze).
Double-width Unicode tiles and ANSI color support for clean rendering.
Diagonal movement with corner-cut prevention.
Spikes placed off the safe path.
Dynamic monsters (👾) that appear along the solution path, move toward the player, and vanish after a few turns. New monsters may spawn every few moves.
Controls: w/a/s/d for cardinal moves, q/e/z/c for diagonals.
r restarts, n creates a new maze, x quits.
Running

Simply execute the script with Python:

Mazegame_midterm.py

Ensure your terminal supports ANSI escape codes and the monster emoji.

Code Organization

The entire gameplay logic lives in a single Python script. The code is structured into helper functions and components that handle:

Maze generation and layout
Pathfinding and game setup
Placement of hazards (spikes and monsters)
Player movement and interaction rules
Rendering the maze and updating the display
Game initialization and the main loop

Docstrings within the code provide more detailed explanations of each component.
