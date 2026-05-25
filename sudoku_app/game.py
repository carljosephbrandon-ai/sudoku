"""Sudoku game state independent from the UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .generator import Board, copy_board, generate_puzzle

Notes = list[list[set[int]]]


def empty_notes() -> Notes:
    return [[set() for _ in range(9)] for _ in range(9)]


@dataclass
class GameState:
    puzzle: Board
    solution: Board
    difficulty: str = "Easy"
    entries: Board | None = None
    notes: Notes = field(default_factory=empty_notes)
    elapsed_seconds: int = 0
    mistakes: int = 0
    paused: bool = False
    completed: bool = False
    completed_recorded: bool = False
    last_started: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if self.entries is None:
            self.entries = copy_board(self.puzzle)

    @classmethod
    def new(cls, difficulty: str = "Easy") -> "GameState":
        puzzle, solution = generate_puzzle(difficulty)
        return cls(puzzle=puzzle, solution=solution, difficulty=difficulty)

    def is_given(self, row: int, col: int) -> bool:
        return self.puzzle[row][col] != 0

    def value_at(self, row: int, col: int) -> int:
        assert self.entries is not None
        return self.entries[row][col]

    def set_value(self, row: int, col: int, value: int) -> bool:
        assert self.entries is not None
        if self.completed or self.paused or self.is_given(row, col):
            return False
        if not 1 <= value <= 9:
            return False
        was_empty_or_different = self.entries[row][col] != value
        self.entries[row][col] = value
        self.notes[row][col].clear()
        if was_empty_or_different and value != self.solution[row][col]:
            self.mistakes += 1
        self.completed = self.is_complete()
        return True

    def erase(self, row: int, col: int) -> bool:
        assert self.entries is not None
        if self.completed or self.paused or self.is_given(row, col):
            return False
        self.entries[row][col] = 0
        return True

    def toggle_note(self, row: int, col: int, value: int) -> bool:
        assert self.entries is not None
        if self.completed or self.paused or self.is_given(row, col) or self.entries[row][col] != 0:
            return False
        if not 1 <= value <= 9:
            return False
        if value in self.notes[row][col]:
            self.notes[row][col].remove(value)
        else:
            self.notes[row][col].add(value)
        return True

    def hint(self, row: int, col: int) -> bool:
        assert self.entries is not None
        if self.completed or self.paused or self.is_given(row, col):
            return False
        self.entries[row][col] = self.solution[row][col]
        self.notes[row][col].clear()
        self.completed = self.is_complete()
        return True

    def is_complete(self) -> bool:
        assert self.entries is not None
        return self.entries == self.solution

    def incorrect_cells(self) -> set[tuple[int, int]]:
        assert self.entries is not None
        cells = set()
        for row in range(9):
            for col in range(9):
                value = self.entries[row][col]
                if value and value != self.solution[row][col]:
                    cells.add((row, col))
        return cells

    def conflict_cells(self) -> set[tuple[int, int]]:
        assert self.entries is not None
        conflicts: set[tuple[int, int]] = set()
        units = []
        units.extend([[(row, col) for col in range(9)] for row in range(9)])
        units.extend([[(row, col) for row in range(9)] for col in range(9)])
        for box_row in range(0, 9, 3):
            for box_col in range(0, 9, 3):
                units.append([(row, col) for row in range(box_row, box_row + 3) for col in range(box_col, box_col + 3)])
        for unit in units:
            seen: dict[int, list[tuple[int, int]]] = {}
            for row, col in unit:
                value = self.entries[row][col]
                if value:
                    seen.setdefault(value, []).append((row, col))
            for cells in seen.values():
                if len(cells) > 1:
                    conflicts.update(cells)
        return conflicts

    def to_dict(self) -> dict:
        return {
            "puzzle": self.puzzle,
            "solution": self.solution,
            "difficulty": self.difficulty,
            "entries": self.entries,
            "notes": [[[n for n in sorted(cell)] for cell in row] for row in self.notes],
            "elapsed_seconds": self.elapsed_seconds,
            "mistakes": self.mistakes,
            "paused": self.paused,
            "completed": self.completed,
            "completed_recorded": self.completed_recorded,
            "last_started": self.last_started,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        notes = [[set(cell) for cell in row] for row in data.get("notes", [])]
        if len(notes) != 9:
            notes = empty_notes()
        return cls(
            puzzle=data["puzzle"],
            solution=data["solution"],
            difficulty=data.get("difficulty", "Easy"),
            entries=data.get("entries"),
            notes=notes,
            elapsed_seconds=int(data.get("elapsed_seconds", 0)),
            mistakes=int(data.get("mistakes", 0)),
            paused=bool(data.get("paused", False)),
            completed=bool(data.get("completed", False)),
            completed_recorded=bool(data.get("completed_recorded", False)),
            last_started=data.get("last_started", datetime.now(timezone.utc).isoformat()),
        )

