# Python Sudoku

A standard-library Tkinter desktop Sudoku app.  This was just a quick test of using Codex because my dad wanted to look at algorithms for populating and solving sudoku.  It builds an executable with pyinstaller, the dev version can build up to 81x81 sudokus (untested), and an interesting thing to note is that in _best_empty_cell of generator.py, the ai did not automatically add the short circuit for if count == 1: return best, but did recognize it would not break anything when I suggested adding it after reviewing the algorithm, which has interesting follow-ons for prompting it differently when implementing in order to minimize/maximize code length, computational optimization, etc. in actual development use.

## Run

```powershell
python -m sudoku_app.main
```

## Features

- Generate Easy, Medium, Hard, and Expert puzzles.
- Play with mouse, keyboard, number buttons, erase, hints, and notes mode.
- Highlights selected rows/columns/boxes, conflicts, and incorrect entries.
- Tracks timer, mistakes, current game autosave, and basic win stats.
- Saves app data to `%APPDATA%\PythonSudoku\sudoku.json` on Windows.

## Test

```powershell
python -m unittest discover -s tests
```

## Packaging

The app has no third-party runtime dependencies. To package it with PyInstaller:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name PythonSudoku run_sudoku.py
```

The executable is created at `dist\PythonSudoku.exe`.
