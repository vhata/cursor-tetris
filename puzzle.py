import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PuzzleGoal:
    """Represents a goal that must be achieved to complete the puzzle."""

    goal_type: str  # "clear_all", "clear_lines", "score", "time", etc.
    target_value: int  # The value that needs to be achieved
    current_value: int = 0  # Current progress towards the goal

    def is_achieved(self) -> bool:
        """Check if the goal has been achieved."""
        return self.current_value >= self.target_value

    def update(self, value: int) -> None:
        """Update progress towards the goal."""
        self.current_value = value


class Puzzle:
    def __init__(
        self,
        name: str,
        description: str,
        grid_data: List[List[Optional[str]]],
        goals: List[PuzzleGoal],
    ):
        self.name = name
        self.description = description
        self.grid_data = grid_data  # None for empty cell, color name for filled cell
        self.goals = goals
        self.validate()

    def validate(self) -> None:
        """Validate puzzle data."""
        # Check grid dimensions
        if not self.grid_data or not self.grid_data[0]:
            raise ValueError("Grid cannot be empty")

        height = len(self.grid_data)
        width = len(self.grid_data[0])

        if height != 20 or width != 10:  # Standard Tetris dimensions
            raise ValueError(f"Invalid grid dimensions: {width}x{height}")

        # Check that all rows have the same width
        if not all(len(row) == width for row in self.grid_data):
            raise ValueError("All rows must have the same width")

        # Check that at least one goal exists
        if not self.goals:
            raise ValueError("Puzzle must have at least one goal")

    def is_completed(self) -> bool:
        """Check if all goals have been achieved."""
        return all(goal.is_achieved() for goal in self.goals)

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> "Puzzle":
        """Create a puzzle from JSON data."""
        goals = [PuzzleGoal(**goal_data) for goal_data in json_data["goals"]]
        return cls(
            name=json_data["name"],
            description=json_data["description"],
            grid_data=json_data["grid_data"],
            goals=goals,
        )

    def to_json(self) -> Dict[str, Any]:
        """Convert puzzle to JSON format."""
        return {
            "name": self.name,
            "description": self.description,
            "grid_data": self.grid_data,
            "goals": [
                {
                    "goal_type": goal.goal_type,
                    "target_value": goal.target_value,
                    "current_value": goal.current_value,
                }
                for goal in self.goals
            ],
        }


def load_puzzle_from_file(filename: str) -> Puzzle:
    """Load a puzzle from a JSON file."""
    with open(filename, "r") as f:
        json_data = json.load(f)
    return Puzzle.from_json(json_data)


def save_puzzle_to_file(puzzle: Puzzle, filename: str) -> None:
    """Save a puzzle to a JSON file."""
    with open(filename, "w") as f:
        json.dump(puzzle.to_json(), f, indent=2)
