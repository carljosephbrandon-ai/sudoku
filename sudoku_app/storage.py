"""JSON persistence for games and stats."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .game import GameState
from .generator import DIFFICULTIES


def app_data_path() -> Path:
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / "PythonSudoku" / "sudoku.json"
    return Path(__file__).resolve().parent.parent / "sudoku_save.json"


def default_stats() -> dict[str, dict[str, Any]]:
    return {
        difficulty: {"games_completed": 0, "best_time": None, "total_wins": 0, "last_played": None}
        for difficulty in DIFFICULTIES
    }


@dataclass
class AppStorage:
    path: Path = field(default_factory=app_data_path)

    def load(self) -> tuple[GameState | None, dict[str, dict[str, Any]]]:
        if not self.path.exists():
            return None, default_stats()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            game = GameState.from_dict(data["current_game"]) if data.get("current_game") else None
            stats = default_stats()
            for difficulty, values in data.get("stats", {}).items():
                if difficulty in stats and isinstance(values, dict):
                    stats[difficulty].update(values)
            return game, stats
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None, default_stats()

    def save(self, game: GameState | None, stats: dict[str, dict[str, Any]]) -> None:
        payload = {"current_game": game.to_dict() if game else None, "stats": stats}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def record_completion(self, game: GameState, stats: dict[str, dict[str, Any]]) -> None:
        bucket = stats.setdefault(game.difficulty, {"games_completed": 0, "best_time": None, "total_wins": 0, "last_played": None})
        bucket["games_completed"] = int(bucket.get("games_completed", 0)) + 1
        bucket["total_wins"] = int(bucket.get("total_wins", 0)) + 1
        best = bucket.get("best_time")
        if best is None or game.elapsed_seconds < int(best):
            bucket["best_time"] = game.elapsed_seconds
        bucket["last_played"] = datetime.now(timezone.utc).isoformat()
        game.completed_recorded = True

