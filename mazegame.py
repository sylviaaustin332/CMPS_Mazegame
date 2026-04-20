"""
TRUE MAZE GAME – Tkinter Graphics Version

A graphical maze game with:
- Multiple difficulty levels
- Monsters that patrol
- Spike hazards
- Personal record tracking
- Level progression
"""

import os
import sys
import random
import time
import tkinter as tk
from tkinter import font
from typing import List, Tuple, Optional
from collections import namedtuple

# =============================
# TILE CONSTANTS
# =============================

WALL = "WALL"
OPEN = "OPEN"
SPIKE = "SPIKE"
START = "START"
EXIT = "EXIT"
PLAYER = "PLAYER"
MONSTER = "MONSTER"

# Colors
COLOR_WALL = "#333333"
COLOR_OPEN = "#f0f0f0"
COLOR_SPIKE = "#ff3333"
COLOR_START = "#33ff33"
COLOR_EXIT = "#ffff33"
COLOR_PLAYER = "#0099ff"
COLOR_MONSTER = "#ff00ff"
TILE_SIZE = 30

# =============================
# DIFFICULTY SETTINGS
# =============================

DIFFICULTY_SETTINGS = {
    1: {"rows": 15, "cols": 29, "spike_fraction": 0.07, "monster_count": 1},
    2: {"rows": 19, "cols": 35, "spike_fraction": 0.10, "monster_count": 1},
    3: {"rows": 23, "cols": 41, "spike_fraction": 0.12, "monster_count": 2},
}

# =============================
# MOVEMENT MAP
# =============================

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

# =============================
# UTILITIES
# =============================

def clear_screen():
    """Clear the console screen in a cross-platform way."""
    os.system("cls" if os.name == "nt" else "clear")

def in_bounds(grid, r, c):
    """Return True if the row/column are within the grid bounds."""
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])

# =============================
# MONSTER
# =============================

Monster = namedtuple("Monster", ["pos", "life"])

# =============================
# GAME STATE FUNCTIONS
# =============================

# =============================
# MAZE GENERATION
# =============================

def generate_true_maze(rows, cols, seed=None):
    """Generate a perfect maze using recursive backtracking.

    The dimensions are rounded up to odd numbers.  A random seed may be
    supplied for reproducible output.  The returned grid uses WALL and OPEN
    constants.
    """
    if seed is not None:
        random.seed(seed)

    if rows % 2 == 0:
        rows += 1
    if cols % 2 == 0:
        cols += 1

    grid = [[WALL for _ in range(cols)] for _ in range(rows)]
    carve_dirs = [(-2,0),(2,0),(0,-2),(0,2)]

    def carve(r, c):
        """Recursive helper carving out passages from (r,c)."""
        grid[r][c] = OPEN
        random.shuffle(carve_dirs)
        for dr, dc in carve_dirs:
            nr, nc = r+dr, c+dc
            if not in_bounds(grid, nr, nc):
                continue
            if grid[nr][nc] == OPEN:
                continue
            grid[r+dr//2][c+dc//2] = OPEN
            carve(nr, nc)

    start_r = random.randrange(1, rows, 2)
    start_c = random.randrange(1, cols, 2)
    carve(start_r, start_c)
    return grid

# =============================
# BFS HELPERS
# =============================

def bfs_farthest_open(grid, start):
    """Return the open cell farthest from start using BFS.

    Used when picking an exit location opposite the start.
    """
    from collections import deque
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
    q = deque([start])
    dist = {start:0}
    farthest = start

    while q:
        r,c = q.popleft()
        if dist[(r,c)] > dist[farthest]:
            farthest = (r,c)
        for dr,dc in dirs:
            nr,nc = r+dr,c+dc
            if not in_bounds(grid,nr,nc):
                continue
            if grid[nr][nc] != OPEN:
                continue
            if (nr,nc) in dist:
                continue
            dist[(nr,nc)] = dist[(r,c)] + 1
            q.append((nr,nc))
    return farthest

def bfs_shortest_path(grid, start, goal):
    """Compute the shortest path between start and goal (inclusive).

    Returns a list of (row,col) positions.  Walls are treated as impassable.
    """
    from collections import deque
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
    q = deque([start])
    parent = {start:None}

    while q:
        r,c = q.popleft()
        if (r,c)==goal:
            break
        for dr,dc in dirs:
            nr,nc = r+dr,c+dc
            if not in_bounds(grid,nr,nc):
                continue
            if grid[nr][nc]==WALL:
                continue
            if (nr,nc) in parent:
                continue
            parent[(nr,nc)] = (r,c)
            q.append((nr,nc))

    if goal not in parent:
        return []

    path=[]
    cur=goal
    while cur:
        path.append(cur)
        cur=parent[cur]
    path.reverse()
    return path

# =============================
# START / EXIT / SPIKES
# =============================

def choose_start_exit(grid):
    """Randomly choose a start location and a farthest exit in the maze.

    Start is any open cell; exit is determined by BFS to maximize distance.
    """
    opens=[(r,c) for r in range(len(grid))
                  for c in range(len(grid[0]))
                  if grid[r][c]==OPEN]
    start=random.choice(opens)
    exit_pos=bfs_farthest_open(grid,start)
    return start,exit_pos

def place_spikes(grid, fraction, start, exit_pos):
    """Scatter spikes randomly in the maze.

    Avoids the safe shortest path from start to exit and stays clear of
    the immediate vicinity of the start.  'fraction' controls density.
    """
    safe_path=set(bfs_shortest_path(grid,start,exit_pos))
    candidates=[]

    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c]!=OPEN:
                continue
            if (r,c) in safe_path:
                continue
            if abs(r-start[0])<=1 and abs(c-start[1])<=1:
                continue
            candidates.append((r,c))

    random.shuffle(candidates)
    spike_count=int(len(candidates)*fraction)

    for r,c in candidates[:spike_count]:
        grid[r][c]=SPIKE

# =============================
# MONSTERS
# =============================

from collections import namedtuple
Monster = namedtuple("Monster", ["pos","life"])

def choose_monsters(grid, start, exit_pos, count=2):
    """Select initial monster positions along the optimal path.

    Each monster is assigned a lifetime (3‑5 turns) and is represented by a
    `Monster` namedtuple.  The path is split evenly so monsters are spread out.
    Monsters avoid positions within 6 Manhattan distance of the start.
    """
    path = bfs_shortest_path(grid, start, exit_pos)
    if not path:
        return []
    # exclude start and exit, and positions within 6 spaces of start
    path = [p for p in path if p not in {start, exit_pos}
            and abs(p[0]-start[0]) + abs(p[1]-start[1]) > 6]
    if not path:
        return []
    # choose indices evenly spaced along path
    if count >= len(path):
        chosen = list(path)
    else:
        step = len(path) / count
        chosen = [path[int(i * step)] for i in range(count)]
    monsters = []
    for pos in chosen:
        life = 5
        monsters.append(Monster(pos, life))
    return monsters


def move_monsters(grid, monsters, player):
    """Age each monster by one turn while keeping them stationary.

    Monsters remain in place for their full lifetime. When a monster's life
    expires it is removed and later respawned elsewhere.
    """
    new_monsters = []
    for m in monsters:
        if m.life - 1 > 0:
            new_monsters.append(Monster(m.pos, m.life - 1))
    return new_monsters


def spawn_monster(grid, start, exit_pos, monsters, player=None):
    """Potentially introduce a new monster mid‑game.

    Chooses a random free cell along the current shortest route from start to
    exit and gives the newcomer a fixed 5-turn lifespan.  Avoids positions
    within 6 spaces of the start and the player's current tile.
    """
    path = bfs_shortest_path(grid, start, exit_pos)
    if not path:
        return monsters
    candidates = [p for p in path if p not in {start, exit_pos}
                  and p not in {m.pos for m in monsters}
                  and abs(p[0]-start[0]) + abs(p[1]-start[1]) > 6
                  and p != player]
    if not candidates:
        return monsters
    pos = random.choice(candidates)
    monsters.append(Monster(pos, 5))
    return monsters

def ensure_monster_count(grid, start, exit_pos, monsters, difficulty, player):
    """Keep the monster count at the desired difficulty level.

    When a monster expires after its 5-turn lifetime, this will spawn a
    replacement so monsters disappear and reappear elsewhere.
    """
    target = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS[1])["monster_count"]
    while len(monsters) < target:
        before_count = len(monsters)
        monsters = spawn_monster(grid, start, exit_pos, monsters, player)
        if len(monsters) == before_count:
            break
    return monsters

# =============================
# BUILD GAME
# =============================

def build_new_game(difficulty=1):
    """Construct and return a fresh maze game state.

    Generates the maze, selects start/exit, places spikes and initial monsters.
    Difficulty level determines maze size, spike density, and monster count.
    Returns grid, start, exit_pos, and a list of monsters.
    """
    settings = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS[1])
    rows = settings["rows"]
    cols = settings["cols"]
    spike_fraction = settings["spike_fraction"]
    monster_count = settings["monster_count"]
    
    grid = generate_true_maze(rows, cols)
    start, exit_pos = choose_start_exit(grid)
    place_spikes(grid, spike_fraction, start, exit_pos)
    grid[start[0]][start[1]] = START
    grid[exit_pos[0]][exit_pos[1]] = EXIT
    monsters = choose_monsters(grid, start, exit_pos, count=monster_count)
    return grid, start, exit_pos, monsters

# =============================
# MOVEMENT
# =============================

def try_move(grid,player,start,delta):
    """Attempt to move the player by delta vector.

    Handles wall collisions, diagonal corner cutting, spikes, and exit.
    Returns the new position and a string result indicating the outcome.
    """
    r,c=player
    dr,dc=delta
    nr,nc=r+dr,c+dc

    if not in_bounds(grid,nr,nc):
        return player,"blocked"

    # Prevent diagonal corner cutting
    if abs(dr)==1 and abs(dc)==1:
        if grid[r+dr][c]==WALL and grid[r][c+dc]==WALL:
            return player,"blocked"

    target=grid[nr][nc]
    if target==WALL:
        return player,"blocked"
    if target==SPIKE:
        return start,"spike"
    if target==EXIT:
        return (nr,nc),"exit"
    return (nr,nc),"moved"

# =============================
# TKINTER GAME WINDOW
# =============================

class MazeGameWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("True Maze Game")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Game state
        self.current_difficulty = 1
        self.level_prs = {1: None, 2: None, 3: None}
        self.grid = None
        self.start = None
        self.exit_pos = None
        self.player = None
        self.monsters = []
        self.steps = 0
        self.game_over = False
        self.message = ""
        self.message_time = 0
        self.level_complete_menu = False
        
        # Create UI
        self.create_widgets()
        self.start_new_level()
        
        # Keyboard binding
        self.root.bind("<Key>", self.on_key)
        
        # Game loop
        self.update_game()
    
    def create_widgets(self):
        # Info frame
        info_frame = tk.Frame(self.root, bg="#333")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.info_label = tk.Label(info_frame, text="", fg="white", bg="#333", 
                                   font=("Arial", 10))
        self.info_label.pack(side=tk.LEFT)
        
        self.steps_label = tk.Label(info_frame, text="Steps: 0", fg="white", bg="#333",
                                    font=("Arial", 10, "bold"))
        self.steps_label.pack(side=tk.RIGHT)
        
        # Canvas
        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Message label
        self.message_label = tk.Label(self.root, text="", fg="black", 
                                      font=("Arial", 12, "bold"))
        self.message_label.pack()
        
        # Controls frame
        controls_frame = tk.Frame(self.root, bg="#f0f0f0")
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        controls_text = "CONTROLS: Q=↖️ W=⬆️ E=↗️ A=⬅️ S=⬇️ D=➡️ Z=↙️ C=↘️ R=Replay  N=Next  X=Exit"
        self.controls_label = tk.Label(controls_frame, text=controls_text, fg="#333", bg="#f0f0f0",
                                       font=("Arial", 9))
        self.controls_label.pack()
    
    def start_new_level(self):
        if self.current_difficulty <= 3:
            self.grid, self.start, self.exit_pos, self.monsters = build_new_game(self.current_difficulty)
            self.player = self.start
            self.steps = 0
            self.game_over = False
            self.message = ""
            self.update_labels()
    
    def update_labels(self):
        info = f"Level {self.current_difficulty}/3 | "
        pr = self.level_prs[self.current_difficulty]
        if pr:
            info += f"PR: {pr} steps"
        else:
            info += "PR: --"
        self.info_label.config(text=info)
        self.steps_label.config(text=f"Steps: {self.steps}")
        
        # Keep level completion messages visible, others expire after 2 seconds
        if self.message:
            if self.level_complete_menu or (time.time() - self.message_time < 2):
                self.message_label.config(text=self.message)
            else:
                self.message_label.config(text="")
        else:
            self.message_label.config(text="")
    
    def draw_maze(self):
        self.canvas.delete("all")
        
        if not self.grid:
            return
        
        # Calculate canvas size
        height = len(self.grid)
        width = len(self.grid[0])
        canvas_width = width * TILE_SIZE
        canvas_height = height * TILE_SIZE
        self.canvas.config(width=canvas_width, height=canvas_height)
        
        # Draw tiles
        monster_positions = {m.pos for m in self.monsters}
        
        for r in range(height):
            for c in range(width):
                x0 = c * TILE_SIZE
                y0 = r * TILE_SIZE
                x1 = x0 + TILE_SIZE
                y1 = y0 + TILE_SIZE
                
                if (r, c) == self.player:
                    if (r, c) == self.start:
                        bg_color = COLOR_START
                    elif (r, c) == self.exit_pos:
                        bg_color = COLOR_EXIT
                    else:
                        bg_color = COLOR_OPEN
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill=bg_color, outline="#ddd")
                    self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text="🧙", 
                                           font=("Arial", 16), fill=COLOR_PLAYER)
                elif (r, c) in monster_positions:
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill=COLOR_OPEN, outline="#ddd")
                    self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text="👾",
                                           font=("Arial", 16), fill="#9933ff")
                elif self.grid[r][c] == WALL:
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill=COLOR_WALL, outline=COLOR_WALL)
                elif self.grid[r][c] == SPIKE:
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill=COLOR_OPEN, outline="#ddd")
                    self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text="^",
                                           font=("Arial", 14, "bold"), fill=COLOR_SPIKE)
                elif self.grid[r][c] == START:
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill=COLOR_START, outline=COLOR_START)
                    self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text="S",
                                           font=("Arial", 14, "bold"), fill="black")
                elif self.grid[r][c] == EXIT:
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill=COLOR_EXIT, outline=COLOR_EXIT)
                    self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text="💎",
                                           font=("Arial", 14), fill="black")
                else:
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill=COLOR_OPEN, outline="#ddd")
    
    def on_key(self, event):
        key = event.char.lower()
        
        if key == "x":
            self.on_close()
            return
        
        # Handle level completion menu FIRST (before game_over check)
        if self.level_complete_menu:
            if key == "r":
                # Replay current level
                self.level_complete_menu = False
                self.start_new_level()
                self.message = "Replaying level..."
                self.message_time = time.time()
                return
            elif key == "n":
                # Go to next level
                if self.current_difficulty < 3:
                    self.level_complete_menu = False
                    self.current_difficulty += 1
                    self.start_new_level()
                    self.message = f"Starting Level {self.current_difficulty}"
                    self.message_time = time.time()
                else:
                    # All levels complete
                    self.level_complete_menu = False
                    self.current_difficulty = 1
                    self.start_new_level()
                    self.message = "Restarting from Level 1"
                    self.message_time = time.time()
                return
            else:
                return
        
        if self.game_over:
            return
        
        if key == "r":
            self.player = self.start
            self.steps = 0
            self.message = "Restarted"
            self.message_time = time.time()
            return
        
        if key == "n":
            self.start_new_level()
            self.message = "New maze"
            self.message_time = time.time()
            return
        
        if key not in MOVE_MAP:
            return
        
        new_pos, result = try_move(self.grid, self.player, self.start, MOVE_MAP[key])
        
        if result == "blocked":
            return
        
        self.player = new_pos
        self.steps += 1
        
        # Check monster collision immediately after move
        monster_positions = {m.pos for m in self.monsters}
        if self.player in monster_positions:
            self.player = self.start
            self.steps = 0
            self.message = "Monster caught you!"
            self.message_time = time.time()
            return
        
        if result == "spike":
            self.player = self.start
            self.steps = 0
            self.message = "Hit a spike!"
            self.message_time = time.time()
            return
        
        if result == "exit":
            self.complete_level()
            return
        
        # Age monsters
        self.monsters = move_monsters(self.grid, self.monsters, self.player)
        if self.steps % 8 == 0:
            self.monsters = ensure_monster_count(self.grid, self.start, self.exit_pos, 
                                                  self.monsters, self.current_difficulty, self.player)
        
        # Check monster collision after movement
        monster_positions = {m.pos for m in self.monsters}
        if self.player in monster_positions:
            self.player = self.start
            self.steps = 0
            self.message = "Monster caught you!"
            self.message_time = time.time()
    
    def complete_level(self):
        # Update personal record
        if self.level_prs[self.current_difficulty] is None or self.steps < self.level_prs[self.current_difficulty]:
            self.level_prs[self.current_difficulty] = self.steps
        
        # Check if this is the final level
        if self.current_difficulty == 3:
            self.message = f"🎊 Congratulations! You have completed the Maze Game! 🎉 Press (r) to replay from Level 1 or (x) to exit"
        else:
            self.message = f"🎉 Level {self.current_difficulty} Complete! {self.steps} steps | Press (r) to replay or (n) for next level"
        
        self.message_time = time.time()
        self.game_over = True
        self.level_complete_menu = True
    
    def update_game(self):
        self.draw_maze()
        self.update_labels()
        self.root.after(50, self.update_game)
    
    def on_close(self):
        self.root.destroy()

# =============================
# MAIN
# =============================

def main():
    root = tk.Tk()
    game = MazeGameWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
