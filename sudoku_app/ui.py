"""Tkinter user interface for the Sudoku app."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .game import GameState
from .generator import DIFFICULTIES
from .storage import AppStorage


class SudokuApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Python Sudoku")
        self.resizable(False, False)
        self.storage = AppStorage()
        loaded_game, self.stats = self.storage.load()
        self.game = loaded_game or GameState.new("Easy")
        self.selected = (0, 0)
        self.notes_mode = tk.BooleanVar(value=False)
        self.difficulty = tk.StringVar(value=self.game.difficulty)
        self.timer_text = tk.StringVar()
        self.status_text = tk.StringVar()
        self.stats_text = tk.StringVar()
        self.cells: list[list[tk.Frame]] = []
        self.value_labels: list[list[tk.Label]] = []
        self.note_labels: list[list[tk.Label]] = []

        self._build()
        self._bind_keys()
        self._refresh()
        self._tick()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self) -> None:
        outer = ttk.Frame(self, padding=12)
        outer.grid(row=0, column=0)

        top = ttk.Frame(outer)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(top, textvariable=self.timer_text, width=12).grid(row=0, column=0, sticky="w")
        ttk.Label(top, textvariable=self.status_text, width=28).grid(row=0, column=1, padx=8)
        ttk.Combobox(top, textvariable=self.difficulty, values=list(DIFFICULTIES), width=10, state="readonly").grid(row=0, column=2)
        ttk.Button(top, text="New Game", command=self._new_game).grid(row=0, column=3, padx=(8, 0))

        board = tk.Frame(outer, bg="#222222", padx=2, pady=2)
        board.grid(row=1, column=0)
        for row in range(9):
            cell_row: list[tk.Frame] = []
            value_row: list[tk.Label] = []
            note_row: list[tk.Label] = []
            for col in range(9):
                pad = (2 if col % 3 == 0 else 1, 2 if row % 3 == 0 else 1, 2 if col == 8 else 1, 2 if row == 8 else 1)
                cell = tk.Frame(board, width=62, height=62, bg="white", padx=1, pady=1)
                cell.grid(row=row, column=col, padx=(pad[0], pad[2]), pady=(pad[1], pad[3]))
                cell.grid_propagate(False)
                value = tk.Label(cell, text="", font=("Segoe UI", 28, "bold"), bg="white")
                value.place(relx=0.5, rely=0.5, anchor="center")
                notes = tk.Label(cell, text="", font=("Consolas", 9), bg="white", justify="center")
                notes.place(relx=0.5, rely=0.5, anchor="center")
                for widget in (cell, value, notes):
                    widget.bind("<Button-1>", lambda _event, r=row, c=col: self._select(r, c))
                cell_row.append(cell)
                value_row.append(value)
                note_row.append(notes)
            self.cells.append(cell_row)
            self.value_labels.append(value_row)
            self.note_labels.append(note_row)

        controls = ttk.Frame(outer)
        controls.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        for value in range(1, 10):
            ttk.Button(controls, text=str(value), width=4, command=lambda v=value: self._input_number(v)).grid(row=0, column=value - 1, padx=2)
        ttk.Button(controls, text="Erase", command=self._erase).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0), padx=2)
        ttk.Checkbutton(controls, text="Notes", variable=self.notes_mode).grid(row=1, column=2, columnspan=2, sticky="ew", pady=(8, 0), padx=2)
        ttk.Button(controls, text="Hint", command=self._hint).grid(row=1, column=4, columnspan=2, sticky="ew", pady=(8, 0), padx=2)
        ttk.Button(controls, text="Pause", command=self._pause_resume).grid(row=1, column=6, columnspan=3, sticky="ew", pady=(8, 0), padx=2)
        ttk.Label(outer, textvariable=self.stats_text).grid(row=3, column=0, sticky="w", pady=(8, 0))

    def _bind_keys(self) -> None:
        self.bind("<Key>", self._on_key)
        self.bind("<Up>", lambda _event: self._move(-1, 0))
        self.bind("<Down>", lambda _event: self._move(1, 0))
        self.bind("<Left>", lambda _event: self._move(0, -1))
        self.bind("<Right>", lambda _event: self._move(0, 1))

    def _select(self, row: int, col: int) -> None:
        self.selected = (row, col)
        self._refresh()

    def _move(self, dr: int, dc: int) -> None:
        row, col = self.selected
        self.selected = ((row + dr) % 9, (col + dc) % 9)
        self._refresh()

    def _on_key(self, event: tk.Event) -> None:
        if event.char and event.char in "123456789":
            self._input_number(int(event.char))
        elif event.keysym in {"BackSpace", "Delete", "0"}:
            self._erase()
        elif event.char and event.char.lower() == "n":
            self.notes_mode.set(not self.notes_mode.get())

    def _input_number(self, value: int) -> None:
        row, col = self.selected
        changed = self.game.toggle_note(row, col, value) if self.notes_mode.get() else self.game.set_value(row, col, value)
        if changed:
            self._after_change()

    def _erase(self) -> None:
        row, col = self.selected
        if self.game.erase(row, col):
            self._after_change()

    def _hint(self) -> None:
        row, col = self.selected
        if self.game.hint(row, col):
            self._after_change()

    def _pause_resume(self) -> None:
        if not self.game.completed:
            self.game.paused = not self.game.paused
            self._after_change()

    def _new_game(self) -> None:
        self.game = GameState.new(self.difficulty.get())
        self.selected = (0, 0)
        self._after_change()

    def _after_change(self) -> None:
        if self.game.completed and not self.game.completed_recorded:
            self.storage.record_completion(self.game, self.stats)
            messagebox.showinfo("Sudoku", "Puzzle complete!")
        self.storage.save(self.game, self.stats)
        self._refresh()

    def _tick(self) -> None:
        if not self.game.paused and not self.game.completed:
            self.game.elapsed_seconds += 1
        self._refresh_timer()
        self.after(1000, self._tick)

    def _refresh_timer(self) -> None:
        minutes, seconds = divmod(self.game.elapsed_seconds, 60)
        self.timer_text.set(f"{minutes:02d}:{seconds:02d}")

    def _refresh(self) -> None:
        incorrect = self.game.incorrect_cells()
        conflicts = self.game.conflict_cells()
        selected_row, selected_col = self.selected
        for row in range(9):
            for col in range(9):
                value = self.game.value_at(row, col)
                is_selected = (row, col) == self.selected
                same_unit = row == selected_row or col == selected_col or (row // 3, col // 3) == (selected_row // 3, selected_col // 3)
                bg = "#dbeafe" if is_selected else "#eef6ff" if same_unit else "white"
                if (row, col) in conflicts:
                    bg = "#ffd7ba"
                if (row, col) in incorrect:
                    bg = "#ffc9c9"
                if self.game.paused:
                    bg = "#eeeeee"
                fg = "#111111" if self.game.is_given(row, col) else "#1d4ed8"
                note_text = self._note_text(row, col) if not self.game.paused and value == 0 else ""
                self.cells[row][col].configure(bg=bg)
                self.value_labels[row][col].configure(bg=bg, fg=fg)
                self.note_labels[row][col].configure(bg=bg, fg="#555555")
                if self.game.paused:
                    self.value_labels[row][col].configure(text="")
                    self.note_labels[row][col].configure(text="")
                    self.value_labels[row][col].place_forget()
                    self.note_labels[row][col].place_forget()
                elif value:
                    self.note_labels[row][col].place_forget()
                    self.value_labels[row][col].configure(text=str(value))
                    self.value_labels[row][col].place(relx=0.5, rely=0.5, anchor="center")
                    self.value_labels[row][col].lift()
                elif note_text.strip():
                    self.value_labels[row][col].place_forget()
                    self.note_labels[row][col].configure(text=note_text)
                    self.note_labels[row][col].place(relx=0.5, rely=0.5, anchor="center")
                    self.note_labels[row][col].lift()
                else:
                    self.value_labels[row][col].configure(text="")
                    self.note_labels[row][col].configure(text="")
                    self.value_labels[row][col].place_forget()
                    self.note_labels[row][col].place_forget()
        self._refresh_timer()
        paused = "Paused" if self.game.paused else "Complete" if self.game.completed else f"Mistakes: {self.game.mistakes}"
        self.status_text.set(f"{self.game.difficulty} - {paused}")
        stats = self.stats.get(self.game.difficulty, {})
        best = stats.get("best_time")
        best_text = "--" if best is None else f"{int(best) // 60:02d}:{int(best) % 60:02d}"
        self.stats_text.set(f"{self.game.difficulty} wins: {stats.get('total_wins', 0)}   Best: {best_text}")

    def _note_text(self, row: int, col: int) -> str:
        values = self.game.notes[row][col]
        lines = []
        for start in (1, 4, 7):
            lines.append(" ".join(str(n) if n in values else " " for n in range(start, start + 3)))
        return "\n".join(lines)

    def _on_close(self) -> None:
        self.storage.save(self.game, self.stats)
        self.destroy()


def run() -> None:
    app = SudokuApp()
    app.mainloop()
