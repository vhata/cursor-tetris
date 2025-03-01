# Tetris

A classic Tetris game implementation in Python using Pygame.

## Requirements

- Python 3.8+
- Pygame

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python tetris.py
```

## Controls

- Left Arrow: Move piece left
- Right Arrow: Move piece right
- Down Arrow: Soft drop
- Up Arrow: Rotate piece
- Space: Hard drop
- P: Pause game
- Q: Quit game

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Planned Features: Puzzle Mode

### Grid Fill Patterns
1. Symmetrical Patterns
   - Mirror image layouts
   - Rotational symmetry
   - Checkerboard patterns with gaps
   - Concentric rings or squares

2. Obstacle Patterns
   - "Wells" (vertical channels that need to be filled)
   - "Bridges" (horizontal gaps at different heights)
   - "Staircases" (ascending or descending patterns)
   - "Islands" (isolated blocks that need to be connected)

3. Shape-based Patterns
   - Letters or numbers to clear
   - Simple geometric shapes (triangles, diamonds)
   - Maze-like patterns
   - Random but controlled density (e.g., 40% filled)

4. Strategic Patterns
   - Pre-placed T-spin setups
   - Chain reaction opportunities
   - "Lock" patterns (requiring specific piece sequences)

### Puzzle Goals
1. Clearing-based Goals
   - Clear all blocks from the grid
   - Clear specific rows or columns
   - Clear blocks of specific colors
   - Clear a minimum number of lines with limited pieces

2. Score-based Goals
   - Achieve a minimum score with limited pieces
   - Get maximum possible score from the setup
   - Chain multiple line clears together

3. Time-based Goals
   - Clear the pattern within a time limit
   - Hold out for a certain duration while clearing lines
   - Achieve specific goals with a piece speed requirement

4. Efficiency Goals
   - Clear the pattern with minimum number of pieces
   - Clear using only specific piece types
   - Achieve the goal without creating any "garbage" lines

5. Combo Goals
   - Create and execute specific T-spin opportunities
   - Achieve back-to-back tetris clears
   - Create a chain reaction of line clears

6. Multi-objective Goals
   - Clear pattern while maintaining a minimum score
   - Clear specific colors while achieving time requirements
   - Complete multiple sub-patterns in a specific order

### Implementation Details
1. Puzzle Definition Format
   - JSON/Array format for grid state
   - Goal conditions and constraints
   - Available piece sequence (if restricted)
   - Time/move limits

2. Difficulty Ratings
   - Easy: Simple patterns, generous constraints
   - Medium: Complex patterns, moderate constraints
   - Hard: Precise execution required, tight constraints
   - Expert: Multiple objectives, very tight constraints

3. Validation System
   - Ensure puzzles are solvable
   - Track minimum solutions
   - Record best scores/times 