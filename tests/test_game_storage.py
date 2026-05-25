import unittest
from pathlib import Path

from sudoku_app.game import GameState
from sudoku_app.storage import AppStorage, default_stats


PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

SOLUTION = [
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


class GameStorageTests(unittest.TestCase):
    def test_game_entries_notes_hint_and_completion(self):
        game = GameState(puzzle=PUZZLE, solution=SOLUTION, difficulty="Easy")
        self.assertFalse(game.set_value(0, 0, 1))
        self.assertTrue(game.set_value(0, 2, 9))
        self.assertIn((0, 2), game.incorrect_cells())
        self.assertEqual(game.mistakes, 1)
        self.assertTrue(game.erase(0, 2))
        self.assertTrue(game.toggle_note(0, 2, 4))
        self.assertEqual(game.notes[0][2], {4})
        self.assertTrue(game.hint(0, 2))
        self.assertEqual(game.value_at(0, 2), 4)
        self.assertEqual(game.notes[0][2], set())

    def test_save_load_round_trip(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            game = GameState(puzzle=PUZZLE, solution=SOLUTION, difficulty="Medium")
            game.toggle_note(0, 2, 4)
            game.elapsed_seconds = 42
            stats = default_stats()
            storage = AppStorage(Path(temp_dir) / "sudoku.json")
            storage.save(game, stats)

            loaded_game, loaded_stats = storage.load()
            self.assertIsNotNone(loaded_game)
            assert loaded_game is not None
            self.assertEqual(loaded_game.difficulty, "Medium")
            self.assertEqual(loaded_game.elapsed_seconds, 42)
            self.assertEqual(loaded_game.notes[0][2], {4})
            self.assertEqual(loaded_stats, stats)

    def test_record_completion_updates_stats(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            game = GameState(puzzle=PUZZLE, solution=SOLUTION, difficulty="Hard")
            game.elapsed_seconds = 120
            stats = default_stats()
            storage = AppStorage(Path(temp_dir) / "sudoku.json")
            storage.record_completion(game, stats)
            self.assertEqual(stats["Hard"]["total_wins"], 1)
            self.assertEqual(stats["Hard"]["games_completed"], 1)
            self.assertEqual(stats["Hard"]["best_time"], 120)
            self.assertTrue(game.completed_recorded)


if __name__ == "__main__":
    unittest.main()
