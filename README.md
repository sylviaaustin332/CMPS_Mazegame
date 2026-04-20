True Maze Game

Sylvia Austin, Shayna Shpits, Lucy Pauze

This is a window-based maze exploration game written in Python. The goal is
to navigate as the player/ wizard (🧙) from a random start (S) to the exit (💎) while avoiding
spikes and transient monsters (👾). 
The game design features three difficulty levels with a personal record tracker following the player's number of moves per level. 

Features
True maze generation using recursive backtracking (perfect maze).
Double-width Unicode tiles and ANSI color support for clean rendering.
Diagonal movement ability to corner-cut.
Spikes placed off the safe path.
Dynamic monsters (👾) that appear randomly and vanish after a few turns. New monsters may spawn every few
moves. Hitting a monster makes the player restart the level. 

Controls: w/a/s/d for cardinal moves, q/e/z/c for diagonals.
r restarts, n creates a new maze, x quits.

Running:

Simply execute the script with Python:
Mazegame_midterm.py

Ensure your terminal supports ANSI escape codes and the monster emoji.

Code Organization

The entire gameplay logic lives in a single Python script (midterm.py).
To keep the code readable, functionality is separated into helper functions
and logical components that handle maze generation, pathfinding, hazard
placement, player movement, rendering, and the main game loop.

Docstrings in the code provide more detailed explanations of each part.
