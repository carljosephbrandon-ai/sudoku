import unittest
from random import Random

from sudoku_app.generator import DIFFICULTIES, clue_count, count_solutions, generate_puzzle, is_valid_board, solve


SOLVED = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]


class GeneratorTests(unittest.TestCase):
    def test_solver_solves_valid_puzzle(self):
        puzzle = [row[:] for row in SOLVED]
        puzzle[0][0] = 0
        puzzle[8][8] = 0
        self.assertEqual(solve(puzzle), SOLVED)

    def test_invalid_board_is_rejected(self):
        board = [row[:] for row in SOLVED]
        board[0][1] = 5
        self.assertFalse(is_valid_board(board))
        self.assertIsNone(solve(board))

    def test_generated_puzzles_are_unique_and_in_range(self):
        for index, difficulty in enumerate(DIFFICULTIES):
            with self.subTest(difficulty=difficulty):
                puzzle, solution = generate_puzzle(difficulty, rng=Random(index))
                self.assertEqual(solve(puzzle), solution)
                self.assertEqual(count_solutions(puzzle, limit=2), 1)
                low, high = DIFFICULTIES[difficulty]
                self.assertLessEqual(low, clue_count(puzzle))
                self.assertLessEqual(clue_count(puzzle), high)

    def test_solver_supports_smaller_square_boards(self):
        puzzle = [
            [1, 0, 0, 4],
            [0, 4, 1, 0],
            [2, 0, 0, 3],
            [0, 3, 2, 0],
        ]
        solution = [
            [1, 2, 3, 4],
            [3, 4, 1, 2],
            [2, 1, 4, 3],
            [4, 3, 2, 1],
        ]
        self.assertEqual(solve(puzzle), solution)


if __name__ == "__main__":
    unittest.main()
