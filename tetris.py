import os
import random
import sys
from typing import Any, List, Optional, Tuple, Union, cast

import pygame

from puzzle import Puzzle, load_puzzle_from_file

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
SOFT_DROP_SCORE = 1  # Points per cell for soft drop
HARD_DROP_SCORE = 2  # Points per cell for hard drop

# Level constants
LINES_PER_LEVEL = 10  # Number of lines needed to advance to next level
BASE_FALL_SPEED = 2.0  # Starting fall speed in seconds (slower start)
SPEED_DECREASE = 0.2  # How much to decrease fall speed per level (more gradual)
MIN_FALL_SPEED = 0.15  # Minimum fall speed (maximum difficulty, slightly more forgiving)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (30, 30, 30)  # Subtle grid color
CYAN = (0, 240, 240)  # Slightly softer colors
BLUE = (0, 0, 240)
ORANGE = (240, 160, 0)
YELLOW = (240, 240, 0)
GREEN = (0, 240, 0)
PURPLE = (160, 0, 240)
RED = (240, 0, 0)

# Shadow colors - 40% opacity (increased from 25%)
SHADOW_COLORS = [
    (0, 240, 240, 102),  # CYAN
    (0, 0, 240, 102),  # BLUE
    (240, 160, 0, 102),  # ORANGE
    (240, 240, 0, 102),  # YELLOW
    (0, 240, 0, 102),  # GREEN
    (160, 0, 240, 102),  # PURPLE
    (240, 0, 0, 102),  # RED
]

# Tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]],  # L
    [[1, 1], [1, 1]],  # O
    [[0, 1, 1], [1, 1, 0]],  # S
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 1, 0], [0, 1, 1]],  # Z
]

COLORS = [CYAN, BLUE, ORANGE, YELLOW, GREEN, PURPLE, RED]


class Tetromino:
    def __init__(self) -> None:
        self.shapes: dict[str, list[list[int]]] = {
            "I": [[1, 1, 1, 1]],
            "O": [[1, 1], [1, 1]],
            "T": [[0, 1, 0], [1, 1, 1]],
            "S": [[0, 1, 1], [1, 1, 0]],
            "Z": [[1, 1, 0], [0, 1, 1]],
            "J": [[1, 0, 0], [1, 1, 1]],
            "L": [[0, 0, 1], [1, 1, 1]],
        }
        self.colors: dict[str, str] = {
            "I": "CYAN",
            "O": "YELLOW",
            "T": "PURPLE",
            "S": "GREEN",
            "Z": "RED",
            "J": "BLUE",
            "L": "ORANGE",
        }
        self.shape_type = random.choice(list(self.shapes.keys()))
        self.shape: list[list[int]] = self.shapes[self.shape_type]
        self.color = COLORS[["I", "J", "L", "O", "S", "T", "Z"].index(self.shape_type)]
        self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0
        self.shape_idx = ["I", "J", "L", "O", "S", "T", "Z"].index(self.shape_type)

    def rotate(self) -> None:
        # Convert the shape to a list of tuples for rotation
        rotated = list(zip(*self.shape[::-1]))
        # Convert back to list of lists
        self.shape = [list(row) for row in rotated]


class TetrisGame:
    def __init__(self, puzzle: Optional[Puzzle] = None) -> None:
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)  # Smaller font for longer text
        # Change grid type to store color tuples instead of strings
        self.grid: List[List[Optional[tuple[int, int, int]]]] = [
            [None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)
        ]
        self.current_piece: Optional[Tetromino] = None
        self.next_piece = Tetromino()  # Initialize with a piece
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.paused = False
        self.pieces_used = 0
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.fall_speed = BASE_FALL_SPEED
        self.puzzle = puzzle
        self.is_puzzle_mode = puzzle is not None
        if self.is_puzzle_mode:
            self.load_puzzle_grid()

        # Create a surface for shadow pieces with alpha channel
        self.shadow_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # Initialize the first piece
        self.current_piece = self.next_piece
        self.next_piece = Tetromino()

        # Check if game is blocked from the start
        if self.check_blockout(self.current_piece):
            self.game_over = True

    def load_puzzle_grid(self) -> None:
        """Load the initial grid state from puzzle data."""
        if not self.puzzle:
            return

        color_map = {
            "CYAN": CYAN,
            "BLUE": BLUE,
            "ORANGE": ORANGE,
            "YELLOW": YELLOW,
            "GREEN": GREEN,
            "PURPLE": PURPLE,
            "RED": RED,
        }
        for y, row in enumerate(self.puzzle.grid_data):
            for x, cell in enumerate(row):
                if cell is not None:
                    color_name = cell.upper()
                    if color_name in color_map:
                        self.grid[y][x] = color_map[color_name]

    def update_puzzle_goals(self) -> None:
        """Update progress on puzzle goals."""
        if not self.is_puzzle_mode or not self.puzzle:
            return

        puzzle = self.puzzle  # Local variable to help type checker
        for goal in puzzle.goals:
            if goal.goal_type == "clear_lines":
                goal.update(self.lines_cleared)
            elif goal.goal_type == "max_pieces":
                # For max_pieces, we check if we're still under the limit
                goal.update(self.pieces_used)
                if goal.current_value > goal.target_value:
                    self.game_over = True
            elif goal.goal_type == "score":
                goal.update(self.score)
            elif goal.goal_type == "pattern":
                # Check if the pattern matches at the specified location
                goal_any = cast(Any, goal)  # Cast to Any to access pattern attributes
                pattern = goal_any.pattern
                pattern_x = goal_any.pattern_x
                pattern_y = goal_any.pattern_y
                matches = 0

                for y in range(len(pattern)):
                    for x in range(len(pattern[0])):
                        grid_y = pattern_y + y
                        grid_x = pattern_x + x

                        if pattern[y][x] is not None:
                            if (
                                grid_y < 0
                                or grid_y >= GRID_HEIGHT
                                or grid_x < 0
                                or grid_x >= GRID_WIDTH
                            ):
                                continue

                            color_name = None
                            if self.grid[grid_y][grid_x] == CYAN:
                                color_name = "CYAN"
                            elif self.grid[grid_y][grid_x] == BLUE:
                                color_name = "BLUE"
                            elif self.grid[grid_y][grid_x] == ORANGE:
                                color_name = "ORANGE"
                            elif self.grid[grid_y][grid_x] == YELLOW:
                                color_name = "YELLOW"
                            elif self.grid[grid_y][grid_x] == GREEN:
                                color_name = "GREEN"
                            elif self.grid[grid_y][grid_x] == PURPLE:
                                color_name = "PURPLE"
                            elif self.grid[grid_y][grid_x] == RED:
                                color_name = "RED"

                            if color_name == pattern[y][x]:
                                matches += 1

                goal.update(matches)

        # Check if all goals are achieved
        # Use a separate check for puzzle completion to help type checker
        if puzzle and puzzle.is_completed():
            self.game_over = True

    def check_blockout(self, piece: Optional[Tetromino]) -> bool:
        """Check if a piece can be placed at its starting position."""
        if not piece:
            return False
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece.x + x
                    new_y = piece.y + y
                    # Check if the position is already occupied
                    if new_y >= 0 and (
                        new_y >= GRID_HEIGHT
                        or new_x < 0
                        or new_x >= GRID_WIDTH
                        or self.grid[new_y][new_x] is not None
                    ):
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
                    1,
                )
                cell_color = self.grid[y][x]
                if cell_color is not None:
                    pygame.draw.rect(
                        self.screen,
                        cell_color,
                        (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE - 1, BLOCK_SIZE - 1),
                    )

    def draw_current_piece(self) -> None:
        if self.current_piece:
            for y, row in enumerate(self.current_piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(
                            self.screen,
                            self.current_piece.color,
                            (
                                (self.current_piece.x + x) * BLOCK_SIZE,
                                (self.current_piece.y + y) * BLOCK_SIZE,
                                BLOCK_SIZE - 1,
                                BLOCK_SIZE - 1,
                            ),
                        )

    def draw_next_piece(self) -> None:
        """Draw next piece preview."""
        if not self.next_piece:
            return

        next_piece_x = GRID_WIDTH * BLOCK_SIZE + BLOCK_SIZE
        next_piece_y = BLOCK_SIZE * 2

        # Draw "Next:" label
        next_label = self.font.render("Next:", True, WHITE)
        self.screen.blit(next_label, (next_piece_x, BLOCK_SIZE))

        # Draw preview box
        pygame.draw.rect(
            self.screen,
            DARK_GRAY,  # Match the grid color
            (next_piece_x, next_piece_y, 4 * BLOCK_SIZE, 4 * BLOCK_SIZE),
            1,
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
                        (
                            center_x + x * BLOCK_SIZE,
                            center_y + y * BLOCK_SIZE,
                            BLOCK_SIZE - 1,
                            BLOCK_SIZE - 1,
                        ),
                    )

    def check_collision(self, x_offset: int = 0, y_offset: int = 0) -> bool:
        if not self.current_piece:
            return False

        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = self.current_piece.x + x + x_offset
                    new_y = self.current_piece.y + y + y_offset
                    if (
                        new_x < 0
                        or new_x >= GRID_WIDTH
                        or new_y >= GRID_HEIGHT
                        or (new_y >= 0 and self.grid[new_y][new_x] is not None)
                    ):
                        return True
        return False

    def lock_piece(self) -> None:
        if not self.current_piece:
            return
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    if self.current_piece.y + y < 0:
                        self.game_over = True
                        return
                    self.grid[self.current_piece.y + y][
                        self.current_piece.x + x
                    ] = self.current_piece.color

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
                MIN_FALL_SPEED, BASE_FALL_SPEED - (SPEED_DECREASE * (self.level - 1))
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

            # Check puzzle goals after clearing lines
            if self.is_puzzle_mode:
                self.update_puzzle_goals()
                if self.puzzle.is_completed():  # type: ignore
                    self.game_over = True

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
                            (
                                (self.current_piece.x + x) * BLOCK_SIZE,
                                (shadow_y + y) * BLOCK_SIZE,
                                BLOCK_SIZE - 1,
                                BLOCK_SIZE - 1,
                            ),
                        )

            # Blit the shadow surface onto the main screen
            self.screen.blit(self.shadow_surface, (0, 0))

    def draw_puzzle_info(self) -> None:
        """Draw puzzle information and goals."""
        if not self.is_puzzle_mode or not self.puzzle:
            return

        y_pos = BLOCK_SIZE * 7  # Start higher up
        sidebar_x = GRID_WIDTH * BLOCK_SIZE + 10
        sidebar_width = SCREEN_WIDTH - sidebar_x - 10  # Leave 10px margin

        # Draw puzzle name (with word wrap if needed)
        words = self.puzzle.name.split()
        lines: List[str] = []
        current_line: List[str] = []

        for word in words:
            test_line = " ".join(current_line + [word])
            if self.font.size(test_line)[0] <= sidebar_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        for line in lines:
            name_surface = self.font.render(line, True, WHITE)
            self.screen.blit(name_surface, (sidebar_x, y_pos))
            y_pos += 30

        y_pos += 20  # Add some spacing

        # Draw pieces used
        pieces_surface = self.font.render(f"Pieces: {self.pieces_used}", True, WHITE)
        self.screen.blit(pieces_surface, (sidebar_x, y_pos))
        y_pos += 40

        # Draw goals
        for goal in self.puzzle.goals:
            color = GREEN if goal.is_achieved() else WHITE
            # Format goal type to be more readable
            goal_type = goal.goal_type.replace("_", " ").title()
            goal_surface = self.small_font.render(
                f"{goal_type}: {goal.current_value}/{goal.target_value}", True, color
            )
            self.screen.blit(goal_surface, (sidebar_x, y_pos))
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
                    if not self.paused and self.current_piece:
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
                            original_shape = self.current_piece.shape[:]
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

            if not self.paused and self.current_piece:
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
                    score_text = self.font.render(f"Score: {self.score}", True, WHITE)
                    level_text = self.font.render(f"Level: {self.level}", True, WHITE)
                    lines_text = self.font.render(f"Lines: {self.lines_cleared}", True, WHITE)

                    self.screen.blit(score_text, (GRID_WIDTH * BLOCK_SIZE + 10, BLOCK_SIZE * 7))
                    self.screen.blit(level_text, (GRID_WIDTH * BLOCK_SIZE + 10, BLOCK_SIZE * 8))
                    self.screen.blit(lines_text, (GRID_WIDTH * BLOCK_SIZE + 10, BLOCK_SIZE * 9))
                else:
                    self.draw_puzzle_info()

                pygame.display.flip()
                self.clock.tick(60)

        # Game over screen
        self.screen.fill(BLACK)
        result_text = (
            "Puzzle Completed!"
            if self.is_puzzle_mode and self.puzzle and self.puzzle.is_completed()
            else "Game Over!"
        )
        game_over_surface = self.font.render(result_text, True, WHITE)
        game_over_rect = game_over_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(game_over_surface, game_over_rect)
        pygame.display.flip()

        # Wait for a moment before returning to menu
        pygame.time.wait(2000)


class Menu:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.state = "main"  # main, instructions
        self.selected_option = 0
        self.main_options = ["Play Game", "Puzzle Mode", "Instructions", "Quit"]
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)

    def draw(self) -> None:
        self.screen.fill(BLACK)

        if self.state == "main":
            # Draw title
            title_surface = self.font.render("TETRIS", True, WHITE)
            title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
            self.screen.blit(title_surface, title_rect)

            # Draw menu options
            for i, option in enumerate(self.main_options):
                color = CYAN if i == self.selected_option else WHITE
                text_surface = self.font.render(option, True, color)
                rect = text_surface.get_rect(
                    center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 60)
                )
                self.screen.blit(text_surface, rect)

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
                "Press ESC to return to menu",
            ]

            for i, line in enumerate(instructions):
                text_surface = self.small_font.render(line, True, WHITE)
                rect = text_surface.get_rect(left=50, top=50 + i * 40)
                self.screen.blit(text_surface, rect)

        pygame.display.flip()

    def handle_input(self) -> Union[str, Tuple[str, Puzzle]]:
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
                            return "puzzle"

                elif self.state == "instructions":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "main"

        return "menu"


class PuzzleMenu(Menu):
    def __init__(self, screen: pygame.Surface) -> None:
        super().__init__(screen)
        self.state = "category_select"  # category_select or puzzle_select
        self.categories: List[Tuple[str, str]] = [
            ("Clearing Puzzles", "Clear specific patterns or lines"),
            ("Speed Puzzles", "Complete objectives within a time limit"),
            ("Piece Limit Puzzles", "Solve puzzles with limited pieces"),
            ("Score Puzzles", "Achieve high scores with specific constraints"),
            ("Pattern Puzzles", "Create specific patterns on the board"),
        ]
        self.selected_category = 0
        self.selected_puzzle = 0
        self.scroll_offset = 0
        self.max_visible = 8
        self.puzzles: List[Puzzle] = []  # Will be loaded when category is selected

    def load_puzzles_for_category(self, category_idx: int) -> List[Puzzle]:
        """Load puzzles for the selected category."""
        puzzles = []
        category_name = self.categories[category_idx][0].lower().replace(" ", "_")
        puzzle_dir = os.path.join("puzzles", category_name)

        if not os.path.exists(puzzle_dir):
            return []

        for filename in sorted(os.listdir(puzzle_dir)):
            if filename.endswith(".json"):
                try:
                    puzzle = load_puzzle_from_file(os.path.join(puzzle_dir, filename))
                    puzzles.append(puzzle)
                except Exception as e:
                    print(f"Error loading puzzle {filename}: {e}")
        return puzzles

    def draw(self) -> None:
        self.screen.fill(BLACK)

        if self.state == "category_select":
            # Draw title
            title_surface = self.font.render("Select Puzzle Type", True, WHITE)
            title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
            self.screen.blit(title_surface, title_rect)

            # Draw category list
            start_y = 120
            for i, (name, desc) in enumerate(self.categories):
                color = CYAN if i == self.selected_category else WHITE

                # Draw category name
                text_surface = self.font.render(name, True, color)
                rect = text_surface.get_rect(left=50, top=start_y + i * 60)
                self.screen.blit(text_surface, rect)

                # Draw category description
                desc_surface = self.small_font.render(desc, True, color)
                desc_rect = desc_surface.get_rect(left=50, top=start_y + i * 60 + 30)
                self.screen.blit(desc_surface, desc_rect)

            # Draw instructions
            back_surface = self.small_font.render("Press ESC to return to menu", True, WHITE)
            back_rect = back_surface.get_rect(bottom=SCREEN_HEIGHT - 20, centerx=SCREEN_WIDTH // 2)
            self.screen.blit(back_surface, back_rect)

        elif self.state == "puzzle_select":
            # Draw title with category name
            category_name = self.categories[self.selected_category][0]
            title_surface = self.font.render(f"Select {category_name}", True, WHITE)
            title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
            self.screen.blit(title_surface, title_rect)

            if not self.puzzles:
                # No puzzles available message
                msg_surface = self.font.render("No puzzles available", True, WHITE)
                msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(msg_surface, msg_rect)
            else:
                # Draw puzzle list
                start_y = 120
                for i in range(min(self.max_visible, len(self.puzzles))):
                    idx = i + self.scroll_offset
                    if idx >= len(self.puzzles):
                        break

                    puzzle = self.puzzles[idx]
                    color = CYAN if idx == self.selected_puzzle else WHITE

                    # Draw puzzle name
                    text_surface = self.font.render(puzzle.name, True, color)
                    rect = text_surface.get_rect(left=50, top=start_y + i * 60)
                    self.screen.blit(text_surface, rect)

                    # Draw puzzle description
                    desc_surface = self.small_font.render(puzzle.description, True, color)
                    desc_rect = desc_surface.get_rect(left=50, top=start_y + i * 60 + 30)
                    self.screen.blit(desc_surface, desc_rect)

                # Draw scroll indicators if needed
                if self.scroll_offset > 0:
                    up_surface = self.font.render("▲", True, WHITE)
                    self.screen.blit(up_surface, (SCREEN_WIDTH - 50, 100))

                if self.scroll_offset + self.max_visible < len(self.puzzles):
                    down_surface = self.font.render("▼", True, WHITE)
                    self.screen.blit(down_surface, (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 100))

            # Draw back instruction
            back_surface = self.small_font.render("Press ESC to return to categories", True, WHITE)
            back_rect = back_surface.get_rect(bottom=SCREEN_HEIGHT - 20, centerx=SCREEN_WIDTH // 2)
            self.screen.blit(back_surface, back_rect)

        pygame.display.flip()

    def handle_input(self) -> Union[str, Tuple[str, Puzzle]]:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if self.state == "category_select":
                    if event.key == pygame.K_UP:
                        self.selected_category = (self.selected_category - 1) % len(self.categories)
                    elif event.key == pygame.K_DOWN:
                        self.selected_category = (self.selected_category + 1) % len(self.categories)
                    elif event.key == pygame.K_RETURN:
                        self.puzzles = self.load_puzzles_for_category(self.selected_category)
                        self.selected_puzzle = 0
                        self.scroll_offset = 0
                        self.state = "puzzle_select"
                    elif event.key == pygame.K_ESCAPE:
                        return "menu"

                elif self.state == "puzzle_select":
                    if event.key == pygame.K_UP:
                        self.selected_puzzle = max(0, self.selected_puzzle - 1)
                        if self.selected_puzzle < self.scroll_offset:
                            self.scroll_offset = self.selected_puzzle
                    elif event.key == pygame.K_DOWN:
                        self.selected_puzzle = min(len(self.puzzles) - 1, self.selected_puzzle + 1)
                        if self.selected_puzzle >= self.scroll_offset + self.max_visible:
                            self.scroll_offset = self.selected_puzzle - self.max_visible + 1
                    elif event.key == pygame.K_RETURN and self.puzzles:
                        return ("puzzle_selected", self.puzzles[self.selected_puzzle])
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "category_select"

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
