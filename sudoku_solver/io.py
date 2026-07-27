"""Reading and writing Sudoku puzzle files."""

from __future__ import annotations

from pathlib import Path

from .board import Board


def load_board(path: str | Path) -> Board:
    puzzle_path = Path(path)
    return Board.from_text(puzzle_path.read_text(encoding="utf-8"))


def save_board(board: Board, path: str | Path) -> None:
    puzzle_path = Path(path)
    puzzle_path.write_text(str(board) + "\n", encoding="utf-8")
