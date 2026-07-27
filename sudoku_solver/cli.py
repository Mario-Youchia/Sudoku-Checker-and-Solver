"""Command-line interface for the Sudoku checker and solver."""

from __future__ import annotations

import argparse
from pathlib import Path

from .board import Board, InvalidPuzzleError, format_board
from .io import load_board, save_board


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check or solve a 9×9 Sudoku puzzle."
    )
    parser.add_argument(
        "puzzle",
        nargs="?",
        type=Path,
        help="Path to a .sdk or text puzzle file.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the puzzle without solving it.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Open the desktop interface.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save the solved board to this file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        board = load_board(args.puzzle) if args.puzzle else Board()
    except (OSError, InvalidPuzzleError) as error:
        print(f"Error: {error}")
        return 2

    if args.gui:
        from .gui import launch

        launch(board)
        return 0

    if args.puzzle is None:
        print("Provide a puzzle file or use --gui.")
        return 2

    if args.check:
        conflicts = board.conflicts()
        if conflicts:
            print(f"Invalid puzzle: {len(conflicts)} cells participate in conflicts.")
            return 1
        print("The puzzle is consistent." if not board.is_complete() else "The completed board is valid.")
        return 0

    if not board.is_consistent():
        print("The puzzle contains row, column, or box conflicts.")
        return 1

    if not board.solve():
        print("No solution exists for this puzzle.")
        return 1

    print(format_board(board))
    print(
        "\nSolved with "
        f"{board.stats.naked_singles} naked singles, "
        f"{board.stats.hidden_singles} hidden singles, "
        f"{board.stats.guesses} guesses, and "
        f"{board.stats.backtracks} backtracks."
    )

    if args.output:
        save_board(board, args.output)
        print(f"Saved: {args.output}")
    return 0
