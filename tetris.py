import pygame
import random
from typing import List, Tuple, Optional
import sys
from puzzle import Puzzle, load_puzzle_from_file
import os

# Initialize Pygame
pygame.init()
pygame.font.init()  # Initialize the font module

# Constants
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH + 6)  # Extra space for next piece preview
SCREEN_HEIGHT = BLOCK_SIZE * GRID_HEIGHT

# Scoring constants
SOFT_DROP_SCORE = 1    # Points per cell for soft drop
HARD_DROP_SCORE = 2    # Points per cell for hard drop

# Level constants
LINES_PER_LEVEL = 10   # Number of lines needed to advance to next level
BASE_FALL_SPEED = 2.0  # Starting fall speed in seconds (slower start)
SPEED_DECREASE = 0.2   # How much to decrease fall speed per level (more gradual)
MIN_FALL_SPEED = 0.15  # Minimum fall speed (maximum difficulty, slightly more forgiving)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (30, 30, 30)  # Subtle grid color
CYAN = (0, 240, 240)      # Slightly softer colors
BLUE = (0, 0, 240)
ORANGE = (240, 160, 0)
YELLOW = (240, 240, 0)
GREEN = (0, 240, 0)
PURPLE = (160, 0, 240)
RED = (240, 0, 0)

# Shadow colors - 40% opacity (increased from 25%)
SHADOW_COLORS = [
    (0, 240, 240, 102),    # CYAN
    (0, 0, 240, 102),      # BLUE
    (240, 160, 0, 102),    # ORANGE
    (240, 240, 0, 102),    # YELLOW
    (0, 240, 0, 102),      # GREEN
    (160, 0, 240, 102),    # PURPLE
    (240, 0, 0, 102)       # RED
]

# Tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],                         # I
    [[1, 0, 0], [1, 1, 1]],                # J
    [[0, 0, 1], [1, 1, 1]],                # L
    [[1, 1], [1, 1]],                      # O
    [[0, 1, 1], [1, 1, 0]],                # S
    [[0, 1, 0], [1, 1, 1]],                # T
    [[1, 1, 0], [0, 1, 1]]                 # Z
]

COLORS = [CYAN, BLUE, ORANGE, YELLOW, GREEN, PURPLE, RED]

class Tetromino:
    def __init__(self):
        self.shape_idx = random.randint(0, len(SHAPES) - 1)
        self.shape = [row[:] for row in SHAPES[self.shape_idx]]
        self.color = COLORS[self.shape_idx]
        self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0

    def rotate(self) -> None:
        self.shape = list(zip(*self.shape[::-1]))

class TetrisGame:
    def __init__(self, puzzle: Optional[Puzzle] = None):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = Tetromino()
        self.next_piece = Tetromino()
        self.game_over = False
        self.paused = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_speed = BASE_FALL_SPEED
        self.pieces_used = 0  # Track number of pieces used for puzzle mode
        
        # Puzzle mode attributes
        self.puzzle = puzzle
        self.is_puzzle_mode = puzzle is not None
        if self.is_puzzle_mode:
            self.load_puzzle_grid()
        
        # Create a surface for shadow pieces with alpha channel
        self.shadow_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Check if game is blocked from the start
        if self.check_blockout(self.current_piece):
            self.game_over = True

    def load_puzzle_grid(self) -> None:
        """Load the initial grid state from puzzle data."""
        color_map = {
            'CYAN': CYAN,
            'BLUE': BLUE,
            'ORANGE': ORANGE,
            'YELLOW': YELLOW,
            'GREEN': GREEN,
            'PURPLE': PURPLE,
            'RED': RED
        }
        for y, row in enumerate(self.puzzle.grid_data):
            for x, cell in enumerate(row):
                if cell is not None:
                    color_name = cell.upper()
                    if color_name in color_map:
                        self.grid[y][x] = color_map[color_name]

    def update_puzzle_goals(self) -> None:
        """Update progress on puzzle goals."""
        if not self.is_puzzle_mode:
            return

        for goal in self.puzzle.goals:
            if goal.goal_type == "clear_lines":
                goal.update(self.lines_cleared)
            elif goal.goal_type == "max_pieces":
                # For max_pieces, we check if we're still under the limit
                goal.update(self.pieces_used)
                if goal.current_value > goal.target_value:
                    self.game_over = True
            elif goal.goal_type == "score":
                goal.update(self.score)

        # Check if all goals are achieved
        if self.puzzle.is_completed():
            self.game_over = True

    def check_blockout(self, piece: Tetromino) -> bool:
        """Check if a piece can be placed at its starting position."""
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece.x + x
                    new_y = piece.y + y
                    # Check if the position is already occupied
                    if new_y >= 0 and (new_y >= GRID_HEIGHT or 
                                     new_x < 0 or 
                                     new_x >= GRID_WIDTH or 
                                     self.grid[new_y][new_x] is not None):
                        return True
        return False

    def add_drop_score(self, distance: int, is_hard_drop: bool = False) -> None:
        """Add score for dropping pieces. Hard drops score more than soft drops."""
        if is_hard_drop:
            self.score += distance * HARD_DROP_SCORE
        else:
            self.score += distance * SOFT_DROP_SCORE

    def draw_grid(self) -> None:
        # Draw the game grid
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                pygame.draw.rect(
                    self.screen,
                    DARK_GRAY,  # Changed from WHITE to DARK_GRAY
                    (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE),
                    1
                )
                if self.grid[y][x]:
                    pygame.draw.rect(
                        self.screen,
                        self.grid[y][x],
                        (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE - 1, BLOCK_SIZE - 1)
                    )

    def draw_current_piece(self) -> None:
        if self.current_piece:
            for y, row in enumerate(self.current_piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(
                            self.screen,
                            self.current_piece.color,
                            ((self.current_piece.x + x) * BLOCK_SIZE,
                             (self.current_piece.y + y) * BLOCK_SIZE,
                             BLOCK_SIZE - 1, BLOCK_SIZE - 1)
                        )

    def draw_next_piece(self) -> None:
        # Draw next piece preview
        next_piece_x = GRID_WIDTH * BLOCK_SIZE + BLOCK_SIZE
        next_piece_y = BLOCK_SIZE * 2
        
        # Draw "Next:" label
        font = pygame.font.Font(None, 36)
        next_label = font.render('Next:', True, WHITE)
        self.screen.blit(next_label, (next_piece_x, BLOCK_SIZE))
        
        # Draw preview box
        pygame.draw.rect(
            self.screen,
            DARK_GRAY,  # Match the grid color
            (next_piece_x, next_piece_y, 4 * BLOCK_SIZE, 4 * BLOCK_SIZE),
            1
        )
        
        # Center the piece in the preview box
        piece_width = len(self.next_piece.shape[0]) * BLOCK_SIZE
        piece_height = len(self.next_piece.shape) * BLOCK_SIZE
        center_x = next_piece_x + (4 * BLOCK_SIZE - piece_width) // 2
        center_y = next_piece_y + (4 * BLOCK_SIZE - piece_height) // 2
        
        # Draw the next piece
        for y, row in enumerate(self.next_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        self.screen,
                        self.next_piece.color,
                        (center_x + x * BLOCK_SIZE,
                         center_y + y * BLOCK_SIZE,
                         BLOCK_SIZE - 1, BLOCK_SIZE - 1)
                    )

    def check_collision(self, x_offset: int = 0, y_offset: int = 0) -> bool:
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = self.current_piece.x + x + x_offset
                    new_y = self.current_piece.y + y + y_offset
                    if (new_x < 0 or new_x >= GRID_WIDTH or
                        new_y >= GRID_HEIGHT or
                        (new_y >= 0 and self.grid[new_y][new_x] is not None)):
                        return True
        return False

    def lock_piece(self) -> None:
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    if self.current_piece.y + y < 0:
                        self.game_over = True
                        return
                    self.grid[self.current_piece.y + y][self.current_piece.x + x] = self.current_piece.color
        
        self.pieces_used += 1  # Increment pieces used counter
        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = Tetromino()
        
        # Check if the new piece can be placed
        if self.check_blockout(self.current_piece):
            self.game_over = True
        
        if self.is_puzzle_mode:
            self.update_puzzle_goals()

    def update_level(self) -> None:
        """Update level based on lines cleared and adjust fall speed."""
        new_level = (self.lines_cleared // LINES_PER_LEVEL) + 1
        if new_level != self.level:
            self.level = new_level
            # Calculate new fall speed with a minimum limit
            self.fall_speed = max(
                MIN_FALL_SPEED,
                BASE_FALL_SPEED - (SPEED_DECREASE * (self.level - 1))
            )

    def clear_lines(self) -> None:
        lines_cleared = 0
        y = GRID_HEIGHT - 1
        while y >= 0:
            if all(cell is not None for cell in self.grid[y]):
                lines_cleared += 1
                for y2 in range(y, 0, -1):
                    self.grid[y2] = self.grid[y2 - 1][:]
                self.grid[0] = [None] * GRID_WIDTH
            else:
                y -= 1
        
        # Update score and level
        if lines_cleared > 0:
            self.score += (100 * lines_cleared) * lines_cleared  # Bonus for multiple lines
            self.lines_cleared += lines_cleared
            self.update_level()

    def get_shadow_position(self) -> int:
        """Calculate the lowest possible position for the current piece."""
        if not self.current_piece:
            return 0
            
        shadow_y = self.current_piece.y
        while not self.check_collision(y_offset=shadow_y - self.current_piece.y + 1):
            shadow_y += 1
        return shadow_y

    def draw_shadow(self) -> None:
        """Draw the shadow of the current piece."""
        if self.current_piece:
            shadow_y = self.get_shadow_position()
            
            # Clear the shadow surface
            self.shadow_surface.fill((0, 0, 0, 0))
            
            # Draw the shadow piece
            for y, row in enumerate(self.current_piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        shadow_color = SHADOW_COLORS[self.current_piece.shape_idx]
                        pygame.draw.rect(
                            self.shadow_surface,
                            shadow_color,
                            ((self.current_piece.x + x) * BLOCK_SIZE,
                             (shadow_y + y) * BLOCK_SIZE,
                             BLOCK_SIZE - 1, BLOCK_SIZE - 1)
                        )
            
            # Blit the shadow surface onto the main screen
            self.screen.blit(self.shadow_surface, (0, 0))

    def draw_puzzle_info(self) -> None:
        """Draw puzzle information and goals."""
        if not self.is_puzzle_mode:
            return

        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 28)  # Smaller font for longer text
        y_pos = BLOCK_SIZE * 7  # Start higher up
        sidebar_x = GRID_WIDTH * BLOCK_SIZE + 10
        sidebar_width = SCREEN_WIDTH - sidebar_x - 10  # Leave 10px margin
        
        # Draw puzzle name (with word wrap if needed)
        words = self.puzzle.name.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= sidebar_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        for line in lines:
            name_text = font.render(line, True, WHITE)
            self.screen.blit(name_text, (sidebar_x, y_pos))
            y_pos += 30
        
        y_pos += 20  # Add some spacing
        
        # Draw pieces used
        pieces_text = font.render(f'Pieces: {self.pieces_used}', True, WHITE)
        self.screen.blit(pieces_text, (sidebar_x, y_pos))
        y_pos += 40
        
        # Draw goals
        for goal in self.puzzle.goals:
            color = GREEN if goal.is_achieved() else WHITE
            # Format goal type to be more readable
            goal_type = goal.goal_type.replace('_', ' ').title()
            goal_text = small_font.render(
                f'{goal_type}: {goal.current_value}/{goal.target_value}',
                True, color
            )
            self.screen.blit(goal_text, (sidebar_x, y_pos))
            y_pos += 30

    def run(self) -> None:
        last_fall_time = pygame.time.get_ticks()
        
        while not self.game_over:
            current_time = pygame.time.get_ticks()
            delta_time = (current_time - last_fall_time) / 1000.0  # Convert to seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return  # Return to menu instead of quitting
                
                if event.type == pygame.KEYDOWN:
                    if not self.paused:
                        if event.key == pygame.K_LEFT:
                            if not self.check_collision(x_offset=-1):
                                self.current_piece.x -= 1
                        elif event.key == pygame.K_RIGHT:
                            if not self.check_collision(x_offset=1):
                                self.current_piece.x += 1
                        elif event.key == pygame.K_DOWN:
                            if not self.check_collision(y_offset=1):
                                start_y = self.current_piece.y
                                self.current_piece.y += 1
                                self.add_drop_score(1)  # Score for each cell dropped
                        elif event.key == pygame.K_UP:
                            original_shape = self.current_piece.shape
                            self.current_piece.rotate()
                            if self.check_collision():
                                self.current_piece.shape = original_shape
                        elif event.key == pygame.K_SPACE:
                            start_y = self.current_piece.y
                            while not self.check_collision(y_offset=1):
                                self.current_piece.y += 1
                            drop_distance = self.current_piece.y - start_y
                            self.add_drop_score(drop_distance, is_hard_drop=True)
                            self.lock_piece()
                            last_fall_time = current_time
                    
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                    elif event.key == pygame.K_q:
                        return  # Return to menu instead of quitting

            if not self.paused:
                if delta_time > self.fall_speed:
                    if not self.check_collision(y_offset=1):
                        self.current_piece.y += 1
                    else:
                        self.lock_piece()
                    last_fall_time = current_time

                # Draw everything
                self.screen.fill(BLACK)
                self.draw_grid()
                self.draw_shadow()
                self.draw_current_piece()
                self.draw_next_piece()
                
                # Draw score and level (if not in puzzle mode)
                if not self.is_puzzle_mode:
                    font = pygame.font.Font(None, 36)
                    score_text = font.render(f'Score: {self.score}', True, WHITE)
                    level_text = font.render(f'Level: {self.level}', True, WHITE)
                    lines_text = font.render(f'Lines: {self.lines_cleared}', True, WHITE)
                    
                    self.screen.blit(score_text, (GRID_WIDTH * BLOCK_SIZE + 10, BLOCK_SIZE * 7))
                    self.screen.blit(level_text, (GRID_WIDTH * BLOCK_SIZE + 10, BLOCK_SIZE * 8))
                    self.screen.blit(lines_text, (GRID_WIDTH * BLOCK_SIZE + 10, BLOCK_SIZE * 9))
                else:
                    self.draw_puzzle_info()

                pygame.display.flip()
                self.clock.tick(60)

        # Game over screen
        self.screen.fill(BLACK)
        font = pygame.font.Font(None, 48)
        
        if self.is_puzzle_mode and self.puzzle.is_completed():
            result_text = "Puzzle Completed!"
        else:
            result_text = "Game Over!"
        
        game_over_text = font.render(result_text, True, WHITE)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(game_over_text, game_over_rect)
        pygame.display.flip()
        
        # Wait for a moment before returning to menu
        pygame.time.wait(2000)

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.state = "main"  # main, instructions
        self.selected_option = 0
        self.main_options = ["Play Game", "Puzzle Mode", "Instructions", "Quit"]
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)

    def draw(self):
        self.screen.fill(BLACK)
        
        if self.state == "main":
            # Draw title
            title = self.font.render("TETRIS", True, WHITE)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
            self.screen.blit(title, title_rect)
            
            # Draw menu options
            for i, option in enumerate(self.main_options):
                color = CYAN if i == self.selected_option else WHITE
                text = self.font.render(option, True, color)
                rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 60))
                self.screen.blit(text, rect)
        
        elif self.state == "instructions":
            # Draw instructions
            instructions = [
                "Controls:",
                "Left/Right Arrow: Move piece",
                "Up Arrow: Rotate piece",
                "Down Arrow: Soft drop",
                "Space: Hard drop",
                "P: Pause game",
                "Q: Quit to menu",
                "",
                "Press ESC to return to menu"
            ]
            
            for i, line in enumerate(instructions):
                text = self.small_font.render(line, True, WHITE)
                rect = text.get_rect(left=50, top=50 + i * 40)
                self.screen.blit(text, rect)
        
        pygame.display.flip()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            if event.type == pygame.KEYDOWN:
                if self.state == "main":
                    if event.key == pygame.K_UP:
                        self.selected_option = (self.selected_option - 1) % len(self.main_options)
                    elif event.key == pygame.K_DOWN:
                        self.selected_option = (self.selected_option + 1) % len(self.main_options)
                    elif event.key == pygame.K_RETURN:
                        if self.main_options[self.selected_option] == "Quit":
                            return "quit"
                        elif self.main_options[self.selected_option] == "Play Game":
                            return "play"
                        elif self.main_options[self.selected_option] == "Instructions":
                            self.state = "instructions"
                        elif self.main_options[self.selected_option] == "Puzzle Mode":
                            return "puzzle"  # We'll implement this later
                
                elif self.state == "instructions":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "main"
        
        return "menu"

class PuzzleMenu(Menu):
    def __init__(self, screen):
        super().__init__(screen)
        self.state = "puzzle_select"
        self.puzzles = self.load_puzzles()
        self.selected_option = 0
        self.scroll_offset = 0
        self.max_visible = 8

    def load_puzzles(self) -> List[Puzzle]:
        """Load all puzzles from the puzzles directory."""
        puzzles = []
        puzzle_dir = "puzzles"
        for filename in sorted(os.listdir(puzzle_dir)):
            if filename.endswith(".json"):
                try:
                    puzzle = load_puzzle_from_file(os.path.join(puzzle_dir, filename))
                    puzzles.append(puzzle)
                except Exception as e:
                    print(f"Error loading puzzle {filename}: {e}")
        return puzzles

    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw title
        title = self.font.render("Select Puzzle", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Draw puzzle list
        start_y = 120
        for i in range(min(self.max_visible, len(self.puzzles))):
            idx = i + self.scroll_offset
            if idx >= len(self.puzzles):
                break
                
            puzzle = self.puzzles[idx]
            color = CYAN if idx == self.selected_option else WHITE
            
            # Draw puzzle name
            text = self.font.render(puzzle.name, True, color)
            rect = text.get_rect(left=50, top=start_y + i * 60)
            self.screen.blit(text, rect)
            
            # Draw puzzle description
            desc = self.small_font.render(puzzle.description, True, color)
            desc_rect = desc.get_rect(left=50, top=start_y + i * 60 + 30)
            self.screen.blit(desc, desc_rect)
        
        # Draw scroll indicators if needed
        if self.scroll_offset > 0:
            up_text = self.font.render("▲", True, WHITE)
            self.screen.blit(up_text, (SCREEN_WIDTH - 50, 100))
        
        if self.scroll_offset + self.max_visible < len(self.puzzles):
            down_text = self.font.render("▼", True, WHITE)
            self.screen.blit(down_text, (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 100))
        
        pygame.display.flip()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_option = max(0, self.selected_option - 1)
                    if self.selected_option < self.scroll_offset:
                        self.scroll_offset = self.selected_option
                elif event.key == pygame.K_DOWN:
                    self.selected_option = min(len(self.puzzles) - 1, self.selected_option + 1)
                    if self.selected_option >= self.scroll_offset + self.max_visible:
                        self.scroll_offset = self.selected_option - self.max_visible + 1
                elif event.key == pygame.K_RETURN:
                    return ("puzzle_selected", self.puzzles[self.selected_option])
                elif event.key == pygame.K_ESCAPE:
                    return "menu"
        
        return "puzzle_menu"

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()
    
    while True:
        menu = Menu(screen)
        # Main menu loop
        while True:
            action = menu.handle_input()
            menu.draw()
            
            if action == "quit":
                pygame.quit()
                sys.exit()
            elif action == "play":
                game = TetrisGame()
                game.run()
                break  # Return to menu after game ends
            elif action == "puzzle":
                puzzle_menu = PuzzleMenu(screen)
                while True:
                    result = puzzle_menu.handle_input()
                    puzzle_menu.draw()
                    
                    if isinstance(result, tuple) and result[0] == "puzzle_selected":
                        game = TetrisGame(puzzle=result[1])
                        game.run()
                        break
                    elif result == "menu":
                        break
                    elif result == "quit":
                        pygame.quit()
                        sys.exit()
                    
                    clock.tick(60)
                break
            
            clock.tick(60) 