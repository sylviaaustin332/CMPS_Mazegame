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
        # Flush any buffered input first
        while msvcrt.kbhit():
            msvcrt.getch()
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

def read_menu_choice():
    """Read a menu choice from the user using standard input.

    This is used for level-completion menus to ensure choices like 'b' are
    received reliably in different terminal environments.
    """
    while True:
        choice = input().strip().lower()
        if choice:
            return choice[0]

def in_bounds(grid, r, c):
    """Return True if the row/column are within the grid bounds."""
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])

# =============================
# RENDERING
# =============================

def get_visible_monsters(monsters):
    """Return set of positions for monsters that should be displayed."""
    return {m.pos for m in monsters} if monsters else set()

def render(grid, player_pos, steps, monsters=None, difficulty=1, personal_record=None):
    """Render the maze to the console.

    Displays walls, open spaces, spikes, start/exit, the player, and any
    active monsters.  'steps' is shown at the top for player feedback.
    Also displays the current difficulty level and personal record for the level.
    """
    clear_screen()
    print(CYAN + "=== TRUE MAZE GAME ===" + RESET)
    print(f"Level: {difficulty}/3" + " | " + (f"Personal Record: {personal_record}" if personal_record else "Personal Record: --"))
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
# MAIN LOOP
# =============================

def main():
    """Main game loop handling input, rendering, and game state updates.

    Supports difficulty progression through 3 levels, personal record tracking
    per level, replay/next level choices, and integrates movement, monster
    logic, and collision responses.
    """
    # Flush any buffered input to prevent stray characters at startup
    import sys
    import io
    try:
        sys.stdin = io.open(sys.stdin.fileno(), encoding=sys.stdin.encoding, errors='ignore')
    except:
        pass
    
    current_difficulty = 1
    level_prs = {1: None, 2: None, 3: None}  # Track personal records per level
    
    while current_difficulty <= 3:
        grid, start, exit_pos, monsters = build_new_game(difficulty=current_difficulty)
        player = start
        steps = 0

        while True:
            render(grid, player, steps, monsters, difficulty=current_difficulty, personal_record=level_prs[current_difficulty])

            if player == exit_pos:
                # Level completed!
                # Update personal record before showing the end-of-level screen
                if level_prs[current_difficulty] is None or steps < level_prs[current_difficulty]:
                    level_prs[current_difficulty] = steps
                    is_new_record = True
                else:
                    is_new_record = False

                render(grid, player, steps, monsters, difficulty=current_difficulty, personal_record=level_prs[current_difficulty])
                print(YELLOW + f"\n🎉 Level {current_difficulty} Complete in {steps} steps!" + RESET)
                if is_new_record:
                    print(GREEN + f"🏆 NEW PERSONAL RECORD!" + RESET)
                else:
                    print(f"PR: {level_prs[current_difficulty]} steps")

                # Offer replay, level navigation, or next-level options
                if current_difficulty < 3:
                    options = "(r)eplay this level or (n)ext level"
                    if current_difficulty > 1:
                        options += " or (b)ack level"
                    options += "?"
                    print(f"\nOptions: {options}")
                    while True:
                        choice = read_menu_choice()
                        if choice == "r":
                            break
                        elif choice == "n":
                            current_difficulty += 1
                            break
                        elif choice == "b" and current_difficulty > 1:
                            current_difficulty -= 1
                            break
                        else:
                            print("Invalid option. Press r, n" + (" or b" if current_difficulty > 1 else "") + ".")
                            continue
                    break  # Exit inner loop to rebuild level or change difficulty
                else:
                    print("\n🏆 CONGRATULATIONS! You've completed all 3 levels!")
                    print("(q)uit to exit, (r)estart from level 1, or (b)ack to level 2?")
                    while True:
                        choice = read_menu_choice()
                        if choice == "q":
                            return
                        elif choice == "r":
                            current_difficulty = 1
                            break
                        elif choice == "b":
                            current_difficulty = 2
                            break
                        else:
                            print("Invalid option. Press q, r, or b.")
                            continue
                    break  # Restart from chosen difficulty
            visible_monsters = get_visible_monsters(monsters)
            if any(player == m.pos for m in monsters if m.pos in visible_monsters):
                render(grid, player, steps, monsters, difficulty=current_difficulty, personal_record=level_prs[current_difficulty])
                print(RED + "👾 You bumped a monster! Returning to start..." + RESET)
                player = start
                steps = 0
                time.sleep(0.8)
                continue

            print("Move: ", end="", flush=True)
            key = read_char()

            if key == "x":
                return
            if key == "r":
                player = start
                steps = 0
                continue
            if key == "n":
                grid, start, exit_pos, monsters = build_new_game(difficulty=current_difficulty)
                player = start
                steps = 0
                continue
            if key not in MOVE_MAP:
                continue

            new_pos, result = try_move(grid, player, start, MOVE_MAP[key])

            if result == "blocked":
                continue

            player = new_pos
            steps += 1

            # immediate collision: player stepped into a visible monster
            visible_monsters = get_visible_monsters(monsters)
            if any(player == m.pos for m in monsters if m.pos in visible_monsters):
                render(grid, player, steps, monsters, difficulty=current_difficulty, personal_record=level_prs[current_difficulty])
                print(RED + "👾 You ran into a monster! Returning to start..." + RESET)
                player = start
                steps = 0
                time.sleep(0.8)
                continue

            # age stationary monsters and occasionally respawn expired ones
            monsters = move_monsters(grid, monsters, player)
            if steps % 8 == 0:
                monsters = ensure_monster_count(grid, start, exit_pos, monsters, current_difficulty, player)

            # check if visible monster moved onto player
            visible_monsters = get_visible_monsters(monsters)
            if any(player == m.pos for m in monsters if m.pos in visible_monsters):
                render(grid, player, steps, monsters, difficulty=current_difficulty, personal_record=level_prs[current_difficulty])
                print(RED + "👾 A monster caught you! Returning to start..." + RESET)
                player = start
                steps = 0
                time.sleep(0.8)
                continue

            if result == "spike":
                render(grid, player, steps, monsters, difficulty=current_difficulty, personal_record=level_prs[current_difficulty])
                print(RED + "💥 Spike! Returning to start..." + RESET)
                time.sleep(0.8)

if __name__=="__main__":
    main()
