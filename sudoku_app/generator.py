"""Sudoku solving and puzzle generation.

The public app still generates classic 9x9 puzzles, but the solver helpers are
size-aware and use iterative search with bitmask constraints instead of
recursive backtracking.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import isqrt
from random import Random

Board = list[list[int]]

DIFFICULTIES: dict[str, tuple[int, int]] = {
    "Easy": (36, 40),
    "Medium": (32, 35),
    "Hard": (28, 31),
    "Expert": (24, 27),
}


@dataclass(frozen=True)
class SudokuSpec:
    size: int
    box_rows: int
    box_cols: int
    full_mask: int

    @classmethod
    def from_board(cls, board: Board) -> "SudokuSpec":
        size = len(board)
        if size == 0 or any(len(row) != size for row in board):
            raise ValueError("Board must be square")
        box_rows, box_cols = _infer_box_shape(size)
        return cls(size=size, box_rows=box_rows, box_cols=box_cols, full_mask=(1 << size) - 1)

    @classmethod
    def classic(cls) -> "SudokuSpec":
        return cls(size=9, box_rows=3, box_cols=3, full_mask=(1 << 9) - 1)

    def box_index(self, row: int, col: int) -> int:
        boxes_per_row = self.size // self.box_cols
        return (row // self.box_rows) * boxes_per_row + (col // self.box_cols)


@dataclass
class SolverState:
    board: Board
    row_masks: list[int]
    col_masks: list[int]
    box_masks: list[int]
    empty_count: int

    def clone(self) -> "SolverState":
        return SolverState(
            board=copy_board(self.board),
            row_masks=self.row_masks[:],
            col_masks=self.col_masks[:],
            box_masks=self.box_masks[:],
            empty_count=self.empty_count,
        )


def empty_board(size: int = 9) -> Board:
    return [[0 for _ in range(size)] for _ in range(size)]


def copy_board(board: Board) -> Board:
    return [row[:] for row in board]


def is_valid_board(board: Board) -> bool:
    try:
        _build_state(board)
    except ValueError:
        return False
    return True


def has_conflicts(board: Board) -> bool:
    return not is_valid_board(board)


def candidates_for(board: Board, row: int, col: int) -> set[int]:
    spec, state = _build_state(board)
    if state.board[row][col]:
        return set()
    return _mask_to_values(_candidate_mask(spec, state, row, col))


def solve(board: Board, *, randomize: bool = False, rng: Random | None = None) -> Board | None:
    solutions = _search(board, limit=1, randomize=randomize, rng=rng)
    return solutions[0] if solutions else None


def count_solutions(board: Board, *, limit: int = 2) -> int:
    return len(_search(board, limit=limit, randomize=False))


def generate_puzzle(difficulty: str = "Easy", rng: Random | None = None) -> tuple[Board, Board]:
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"Unknown difficulty: {difficulty}")
    rng = rng or Random()
    min_givens, max_givens = DIFFICULTIES[difficulty]
    target_givens = rng.randint(min_givens, max_givens)

    solution = solve(empty_board(), randomize=True, rng=rng)
    if solution is None:
        raise RuntimeError("Could not generate solved Sudoku board")
    puzzle = deepcopy(solution)

    cells = [(row, col) for row in range(9) for col in range(9)]
    rng.shuffle(cells)
    givens = 81

    for row, col in cells:
        if givens <= target_givens:
            break
        old_value = puzzle[row][col]
        puzzle[row][col] = 0
        if count_solutions(puzzle, limit=2) != 1:
            puzzle[row][col] = old_value
        else:
            givens -= 1

    return puzzle, solution


def clue_count(board: Board) -> int:
    return sum(1 for row in board for value in row if value)


def _search(board: Board, *, limit: int, randomize: bool, rng: Random | None = None) -> list[Board]:
    if limit <= 0:
        return []
    try:
        spec, initial = _build_state(board)
    except ValueError:
        return []

    rng = rng or Random()
    solutions: list[Board] = []
    stack = [initial]

    while stack and len(solutions) < limit:
        state = stack.pop()
        if not _propagate_singles(spec, state):
            continue
        if state.empty_count == 0:
            solutions.append(copy_board(state.board))
            continue

        choice = _best_empty_cell(spec, state)
        if choice is None:
            continue
        row, col, mask = choice
        values = list(_mask_to_values(mask))
        if randomize:
            rng.shuffle(values)

        # Stack is LIFO, so reverse preserves randomized/ascending attempt order.
        for value in reversed(values):
            next_state = state.clone()
            if _place_value(spec, next_state, row, col, value):
                stack.append(next_state)

    return solutions


def _build_state(board: Board) -> tuple[SudokuSpec, SolverState]:
    spec = SudokuSpec.from_board(board)
    row_masks = [0 for _ in range(spec.size)]
    col_masks = [0 for _ in range(spec.size)]
    box_masks = [0 for _ in range(spec.size)]
    working = copy_board(board)
    empty_count = 0

    for row in range(spec.size):
        for col in range(spec.size):
            value = working[row][col]
            if value == 0:
                empty_count += 1
                continue
            if not 1 <= value <= spec.size:
                raise ValueError("Cell value outside board range")
            bit = _value_bit(value)
            box = spec.box_index(row, col)
            if row_masks[row] & bit or col_masks[col] & bit or box_masks[box] & bit:
                raise ValueError("Board contains duplicate values")
            row_masks[row] |= bit
            col_masks[col] |= bit
            box_masks[box] |= bit

    return spec, SolverState(working, row_masks, col_masks, box_masks, empty_count)


def _propagate_singles(spec: SudokuSpec, state: SolverState) -> bool:
    changed = True
    while changed:
        changed = False
        for row in range(spec.size):
            for col in range(spec.size):
                if state.board[row][col] != 0:
                    continue
                mask = _candidate_mask(spec, state, row, col)
                if mask == 0:
                    return False
                if _single_bit(mask):
                    if not _place_value(spec, state, row, col, mask.bit_length()):
                        return False
                    changed = True
    return True


def _best_empty_cell(spec: SudokuSpec, state: SolverState) -> tuple[int, int, int] | None:
    best: tuple[int, int, int] | None = None
    best_count = spec.size + 1
    for row in range(spec.size):
        for col in range(spec.size):
            if state.board[row][col] == 0:
                mask = _candidate_mask(spec, state, row, col)
                count = mask.bit_count()
                if count == 0:
                    return row, col, 0
                if count < best_count:
                    best = row, col, mask
                    best_count = count
                    if count == 1:
                        return best
    return best


def _candidate_mask(spec: SudokuSpec, state: SolverState, row: int, col: int) -> int:
    used = state.row_masks[row] | state.col_masks[col] | state.box_masks[spec.box_index(row, col)]
    return spec.full_mask & ~used


def _place_value(spec: SudokuSpec, state: SolverState, row: int, col: int, value: int) -> bool:
    if state.board[row][col] != 0:
        return False
    bit = _value_bit(value)
    box = spec.box_index(row, col)
    if (state.row_masks[row] | state.col_masks[col] | state.box_masks[box]) & bit:
        return False
    state.board[row][col] = value
    state.row_masks[row] |= bit
    state.col_masks[col] |= bit
    state.box_masks[box] |= bit
    state.empty_count -= 1
    return True


def _value_bit(value: int) -> int:
    return 1 << (value - 1)


def _single_bit(mask: int) -> bool:
    return mask != 0 and mask & (mask - 1) == 0


def _mask_to_values(mask: int) -> set[int]:
    values: set[int] = set()
    value = 1
    while mask:
        if mask & 1:
            values.add(value)
        mask >>= 1
        value += 1
    return values


def _infer_box_shape(size: int) -> tuple[int, int]:
    root = isqrt(size)
    if root * root == size:
        return root, root
    for rows in range(root, 0, -1):
        if size % rows == 0:
            return rows, size // rows
    raise ValueError("Could not infer Sudoku box shape")
