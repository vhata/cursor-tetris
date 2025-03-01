import pygame
import random
from typing import List, Tuple, Optional
import sys

# Initialize Pygame
pygame.init()

# Constants
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH + 6)  # Extra space for next piece preview
SCREEN_HEIGHT = BLOCK_SIZE * GRID_HEIGHT

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
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = Tetromino()
        self.next_piece = Tetromino()
        self.game_over = False
        self.paused = False
        self.score = 0
        self.fall_time = 0
        self.fall_speed = 0.5  # Time in seconds between automatic drops
        
        # Create a surface for shadow pieces with alpha channel
        self.shadow_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    def add_drop_score(self, distance: int, is_hard_drop: bool = False) -> None:
        """Add score for dropping pieces. Hard drops score more than soft drops."""
        if is_hard_drop:
            self.score += distance * 2  # 2 points per cell for hard drop
        else:
            self.score += distance  # 1 point per cell for soft drop

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
        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = Tetromino()

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
        
        # Update score
        if lines_cleared > 0:
            self.score += (100 * lines_cleared) * lines_cleared  # Bonus for multiple lines

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

    def run(self) -> None:
        last_fall_time = pygame.time.get_ticks()
        
        while not self.game_over:
            current_time = pygame.time.get_ticks()
            delta_time = (current_time - last_fall_time) / 1000.0  # Convert to seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
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
                        pygame.quit()
                        sys.exit()

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
                self.draw_shadow()  # Draw shadow before the current piece
                self.draw_current_piece()
                self.draw_next_piece()
                
                # Draw score
                font = pygame.font.Font(None, 36)
                score_text = font.render(f'Score: {self.score}', True, WHITE)
                self.screen.blit(score_text, (GRID_WIDTH * BLOCK_SIZE + 10, BLOCK_SIZE * 7))

                pygame.display.flip()
                self.clock.tick(60)

        # Game over screen
        font = pygame.font.Font(None, 48)
        game_over_text = font.render('Game Over!', True, WHITE)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(game_over_text, game_over_rect)
        pygame.display.flip()
        
        # Wait for a moment before quitting
        pygame.time.wait(2000)
        pygame.quit()

if __name__ == "__main__":
    game = TetrisGame()
    game.run() 