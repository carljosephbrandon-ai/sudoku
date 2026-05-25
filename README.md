# Python Sudoku

A standard-library Tkinter desktop Sudoku app.

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
