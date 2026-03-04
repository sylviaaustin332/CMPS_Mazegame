"""
TRUE MAZE GAME – Polished Version

Upgrades:
- Double-width tiles for perfect alignment
- ANSI color support
- Fixed diagonal corner cutting
- Improved spike placement
- Cleaner rendering
"""

import os
import sys
import random
import time
from typing import List, Tuple, Optional

# =============================
# ANSI COLORS
# =============================

RESET = "\033[0m"
GRAY = "\033[90m"
RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"  # color for monsters

# =============================
# TILE CONSTANTS (2-char wide)
# =============================

WALL = "██"
OPEN = "  "
SPIKE = "^^"
START = "SS"
EXIT = "EE"
PLAYER = "@@"
MONSTER = "👾"  # emoji for monsters (double width)
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
    """Clear the console screen in a cross-platform way.

    Uses 'cls' on Windows and 'clear' on Unix-like systems.
    """
    os.system("cls" if os.name == "nt" else "clear")

def read_char():
    """Read a single character from standard input without requiring Enter.

    Falls back to a Unix-compatible implementation when msvcrt is unavailable.
    Returned character is lowercased for uniform command handling.
    """
    try:
        import msvcrt
        ch = msvcrt.getch()
        return ch.decode("utf-8").lower()
    except ImportError:
        import tty
        import termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

def in_bounds(grid, r, c):
    """Return True if the row/column are within the grid bounds."""
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])

# =============================
# RENDERING
# =============================

def render(grid, player_pos, steps, monsters=None):
    """Render the maze to the console.

    Displays walls, open spaces, spikes, start/exit, the player, and any
    active monsters.  'steps' is shown at the top for player feedback.
    """
    clear_screen()
    print(CYAN + "=== TRUE MAZE GAME ===" + RESET)
    print("Controls: w/a/s/d, q/e/z/c (diagonals)")
    print("r = restart | n = new maze | x = quit")
    print(f"Steps: {steps}\n")

    pr, pc = player_pos
    monster_set = {m.pos for m in monsters} if monsters else set()

    for r, row in enumerate(grid):
        line = []
        for c, ch in enumerate(row):
            if (r, c) == (pr, pc):
                line.append(CYAN + PLAYER + RESET)
            elif (r, c) in monster_set:
                line.append(MAGENTA + MONSTER + RESET)
            elif ch == WALL:
                line.append(GRAY + WALL + RESET)
            elif ch == SPIKE:
                line.append(RED + SPIKE + RESET)
            elif ch == START:
                line.append(GREEN + START + RESET)
            elif ch == EXIT:
                line.append(YELLOW + EXIT + RESET)
            else:
                line.append(OPEN)
        print("".join(line))
    print()

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
    """
    path = bfs_shortest_path(grid, start, exit_pos)
    if not path:
        return []
    # exclude start and exit
    path = [p for p in path if p not in {start, exit_pos}]
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
        life = random.randint(3,5)
        monsters.append(Monster(pos, life))
    return monsters


def move_monsters(grid, monsters, player):
    """Move each monster closer to the player and age them by one turn.

    Monsters attempt to reduce Manhattan distance to the player without
    walking through blocked tiles or other monsters.  Those whose life
    expires are removed from the returned list.
    """
    new_monsters = []
    occupied = {m.pos for m in monsters}
    for m in monsters:
        r,c = m.pos
        # find possible moves
        candidates = []
        for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr,nc = r+dr, c+dc
            if not in_bounds(grid,nr,nc):
                continue
            if grid[nr][nc] in (WALL, SPIKE, START, EXIT):
                continue
            if (nr,nc) in occupied:
                continue
            candidates.append((nr,nc))
        if candidates:
            def manh(p):
                return abs(p[0]-player[0]) + abs(p[1]-player[1])
            best_dist = manh(m.pos)
            best_moves = []
            for pos in candidates:
                d = manh(pos)
                if d < best_dist:
                    best_dist = d
                    best_moves = [pos]
                elif d == best_dist:
                    best_moves.append(pos)
            if best_moves:
                new_pos = random.choice(best_moves)
            else:
                new_pos = random.choice(candidates)
        else:
            new_pos = m.pos
        occupied.add(new_pos)
        # decrease life
        if m.life - 1 > 0:
            new_monsters.append(Monster(new_pos, m.life - 1))
        # else it vanishes automatically
    return new_monsters


def spawn_monster(grid, start, exit_pos, monsters):
    """Potentially introduce a new monster mid‑game.

    Chooses a random free cell along the current shortest route from start to
    exit and gives the newcomer a short lifespan.  Called periodically from
    the main loop to keep the maze dynamic.
    """
    path = bfs_shortest_path(grid, start, exit_pos)
    if not path:
        return monsters
    candidates = [p for p in path if p not in {start, exit_pos}
                  and p not in {m.pos for m in monsters}]
    if not candidates:
        return monsters
    pos = random.choice(candidates)
    life = random.randint(3,5)
    monsters.append(Monster(pos, life))
    return monsters

# =============================
# BUILD GAME
# =============================

def build_new_game(rows=15,cols=29,spike_fraction=0.07, monster_count=None):
    """Construct and return a fresh maze game state.

    Generates the maze, selects start/exit, places spikes and initial monsters.
    Returns grid, start, exit_pos, and a list of monsters.
    """
    grid=generate_true_maze(rows,cols)
    start,exit_pos=choose_start_exit(grid)
    place_spikes(grid,spike_fraction,start,exit_pos)
    grid[start[0]][start[1]]=START
    grid[exit_pos[0]][exit_pos[1]]=EXIT
    if monster_count is None:
        monster_count = random.choice([2,3])
    monsters=choose_monsters(grid,start,exit_pos,count=monster_count)
    return grid,start,exit_pos,monsters

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
# MAIN LOOP
# =============================

def main():
    """Main game loop handling input, rendering, and game state updates.

    Supports restart, new maze, quitting, and integrates movement, monster
    logic, and collision responses.
    """
    grid,start,exit_pos,monsters=build_new_game()
    player=start
    steps=0

    while True:
        render(grid,player,steps,monsters)

        if player==exit_pos:
            print(YELLOW+f"🎉 You escaped in {steps} steps!"+RESET)
            break

        # check monster collision (alive monsters only)
        if any(player == m.pos for m in monsters):
            render(grid,player,steps,monsters)
            print(RED+"👾 You bumped a monster! Returning to start..."+RESET)
            player=start
            steps=0
            time.sleep(0.8)
            continue

        print("Move: ",end="",flush=True)
        key=read_char()

        if key=="x":
            break
        if key=="r":
            player=start
            steps=0
            continue
        if key=="n":
            grid,start,exit_pos,monsters=build_new_game()
            player=start
            steps=0
            continue
        if key not in MOVE_MAP:
            continue

        new_pos,result=try_move(grid,player,start,MOVE_MAP[key])

        if result=="blocked":
            continue

        player=new_pos
        steps+=1

        # immediate collision: player stepped into a monster
        if any(player == m.pos for m in monsters):
            render(grid,player,steps,monsters)
            print(RED+"👾 You ran into a monster! Returning to start..."+RESET)
            player=start
            steps=0
            time.sleep(0.8)
            continue

        # move monsters after player moves
        monsters = move_monsters(grid, monsters, player)

        # possibly spawn another monster every 3 steps
        if steps % 3 == 0:
            monsters = spawn_monster(grid, start, exit_pos, monsters)

        # check if monster moved onto player
        if any(player == m.pos for m in monsters):
            render(grid,player,steps,monsters)
            print(RED+"👾 A monster caught you! Returning to start..."+RESET)
            player=start
            steps=0
            time.sleep(0.8)
            continue

        if result=="spike":
            render(grid,player,steps,monsters)
            print(RED+"💥 Spike! Returning to start..."+RESET)
            time.sleep(0.8)

if __name__=="__main__":
    main()
