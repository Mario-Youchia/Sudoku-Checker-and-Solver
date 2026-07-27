"""Tests for Sudoku parsing, checking, and solving."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sudoku_solver.board import Board, InvalidPuzzleError
from sudoku_solver.io import load_board, save_board


class BoardParsingTests(unittest.TestCase):
    def test_round_trip_rows(self) -> None:
        rows = [
            "53..7....",
            "6..195...",
            ".98....6.",
            "8...6...3",
            "4..8.3..1",
            "7...2...6",
            ".6....28.",
            "...419..5",
            "....8..79",
        ]
        self.assertEqual(Board.from_rows(rows).rows(), rows)

    def test_rejects_wrong_row_count(self) -> None:
        with self.assertRaises(InvalidPuzzleError):
            Board.from_rows(["........."] * 8)

    def test_rejects_invalid_character(self) -> None:
        rows = ["........."] * 8 + ["....x...."]
        with self.assertRaises(InvalidPuzzleError):
            Board.from_rows(rows)


class BoardValidationTests(unittest.TestCase):
    def test_valid_incomplete_board(self) -> None:
        board = Board.from_rows([
            "...26.7.1",
            "68..7..9.",
            "19...45..",
            "82.1...4.",
            "..46.29..",
            ".5...3.28",
            "..93...74",
            ".4..5..36",
            "7.3.18...",
        ])
        self.assertTrue(board.is_consistent())
        self.assertFalse(board.is_complete())

    def test_row_conflict(self) -> None:
        board = Board.from_rows(["11......."] + ["........."] * 8)
        self.assertEqual(board.conflicts(), {(0, 0), (0, 1)})

    def test_column_conflict(self) -> None:
        board = Board.from_rows(["1........", "1........"] + ["........."] * 7)
        self.assertEqual(board.conflicts(), {(0, 0), (1, 0)})

    def test_box_conflict(self) -> None:
        board = Board.from_rows(["1........", ".1......."] + ["........."] * 7)
        self.assertEqual(board.conflicts(), {(0, 0), (1, 1)})


class SolverTests(unittest.TestCase):
    def test_solves_easy_puzzle(self) -> None:
        board = Board.from_rows([
            "...26.7.1",
            "68..7..9.",
            "19...45..",
            "82.1...4.",
            "..46.29..",
            ".5...3.28",
            "..93...74",
            ".4..5..36",
            "7.3.18...",
        ])
        self.assertTrue(board.solve())
        self.assertTrue(board.is_solved())
        self.assertEqual(board.rows()[0], "435269781")

    def test_solves_search_puzzle(self) -> None:
        board = Board.from_rows([
            "....5..1.",
            "2........",
            "5.19..48.",
            "6...1.24.",
            "8.......7",
            ".23.4...1",
            ".69..28.3",
            "........4",
            ".4..8....",
        ])
        self.assertTrue(board.solve())
        self.assertEqual(board.rows(), [
            "497856312",
            "286134795",
            "531927486",
            "675319248",
            "814265937",
            "923748561",
            "169472853",
            "758693124",
            "342581679",
        ])

    def test_unsatisfiable_puzzle_is_preserved(self) -> None:
        rows = ["11......."] + ["........."] * 8
        board = Board.from_rows(rows)
        self.assertFalse(board.solve())
        self.assertEqual(board.rows(), rows)

    def test_file_round_trip(self) -> None:
        board = Board.from_rows(["........."] * 9)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "puzzle.sdk"
            save_board(board, path)
            self.assertEqual(load_board(path).rows(), board.rows())


if __name__ == "__main__":
    unittest.main()
