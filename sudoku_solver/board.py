"""Sudoku board validation and solving logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

BOARD_SIZE = 9
BOX_SIZE = 3
EMPTY = 0
DIGITS = frozenset(range(1, 10))

Position = tuple[int, int]


def _build_units() -> tuple[tuple[Position, ...], ...]:
    rows = [tuple((row, col) for col in range(BOARD_SIZE)) for row in range(BOARD_SIZE)]
    columns = [
        tuple((row, col) for row in range(BOARD_SIZE))
        for col in range(BOARD_SIZE)
    ]
    boxes = []
    for box_row in range(0, BOARD_SIZE, BOX_SIZE):
        for box_col in range(0, BOARD_SIZE, BOX_SIZE):
            boxes.append(
                tuple(
                    (row, col)
                    for row in range(box_row, box_row + BOX_SIZE)
                    for col in range(box_col, box_col + BOX_SIZE)
                )
            )
    return tuple(rows + columns + boxes)


UNITS = _build_units()
CELL_UNITS: dict[Position, tuple[tuple[Position, ...], ...]] = {
    (row, col): tuple(unit for unit in UNITS if (row, col) in unit)
    for row in range(BOARD_SIZE)
    for col in range(BOARD_SIZE)
}


class InvalidPuzzleError(ValueError):
    """Raised when a puzzle cannot be represented as a valid 9×9 grid."""


@dataclass(slots=True)
class SolveStats:
    """Counts the main solving operations."""

    naked_singles: int = 0
    hidden_singles: int = 0
    guesses: int = 0
    backtracks: int = 0


class Board:
    """A mutable 9×9 Sudoku board."""

    def __init__(self, rows: Sequence[Sequence[int]] | None = None) -> None:
        if rows is None:
            self._grid = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        else:
            self._grid = self._validated_grid(rows)
        self.stats = SolveStats()

    @staticmethod
    def _validated_grid(rows: Sequence[Sequence[int]]) -> list[list[int]]:
        if len(rows) != BOARD_SIZE:
            raise InvalidPuzzleError("A Sudoku puzzle must contain exactly 9 rows.")

        grid: list[list[int]] = []
        for row_index, row in enumerate(rows, start=1):
            if len(row) != BOARD_SIZE:
                raise InvalidPuzzleError(
                    f"Row {row_index} must contain exactly 9 cells."
                )
            parsed_row: list[int] = []
            for value in row:
                if isinstance(value, bool) or not isinstance(value, int):
                    raise InvalidPuzzleError("Cells must be integers from 0 to 9.")
                if value not in range(10):
                    raise InvalidPuzzleError("Cells must be integers from 0 to 9.")
                parsed_row.append(value)
            grid.append(parsed_row)
        return grid

    @classmethod
    def from_rows(cls, rows: Sequence[str]) -> "Board":
        """Create a board from nine strings using digits and '.' or '0' for blanks."""
        if len(rows) != BOARD_SIZE:
            raise InvalidPuzzleError("A Sudoku puzzle must contain exactly 9 rows.")

        parsed: list[list[int]] = []
        for row_index, raw_row in enumerate(rows, start=1):
            row = raw_row.strip().replace(" ", "")
            if len(row) != BOARD_SIZE:
                raise InvalidPuzzleError(
                    f"Row {row_index} must contain exactly 9 cells."
                )
            if any(character not in "123456789.0" for character in row):
                raise InvalidPuzzleError(
                    f"Row {row_index} contains an unsupported character."
                )
            parsed.append([EMPTY if character in ".0" else int(character) for character in row])
        return cls(parsed)

    @classmethod
    def from_text(cls, text: str) -> "Board":
        """Create a board from text containing nine non-empty rows."""
        rows = [line.strip() for line in text.splitlines() if line.strip()]
        return cls.from_rows(rows)

    def copy(self) -> "Board":
        clone = Board(self._grid)
        clone.stats = SolveStats(
            naked_singles=self.stats.naked_singles,
            hidden_singles=self.stats.hidden_singles,
            guesses=self.stats.guesses,
            backtracks=self.stats.backtracks,
        )
        return clone

    def rows(self) -> list[str]:
        """Return the board using '.' for empty cells."""
        return [
            "".join(str(value) if value else "." for value in row)
            for row in self._grid
        ]

    def values(self) -> list[list[int]]:
        """Return a detached copy of the numeric grid."""
        return [row.copy() for row in self._grid]

    def value_at(self, row: int, col: int) -> int:
        return self._grid[row][col]

    def set_value(self, row: int, col: int, value: int) -> None:
        if value not in range(10):
            raise ValueError("A cell value must be between 0 and 9.")
        self._grid[row][col] = value

    def empty_positions(self) -> list[Position]:
        return [
            (row, col)
            for row in range(BOARD_SIZE)
            for col in range(BOARD_SIZE)
            if self._grid[row][col] == EMPTY
        ]

    def conflicts(self) -> set[Position]:
        """Return every cell participating in a duplicate row, column, or box."""
        conflicts: set[Position] = set()
        for unit in UNITS:
            positions_by_value: dict[int, list[Position]] = {}
            for row, col in unit:
                value = self._grid[row][col]
                if value:
                    positions_by_value.setdefault(value, []).append((row, col))
            for positions in positions_by_value.values():
                if len(positions) > 1:
                    conflicts.update(positions)
        return conflicts

    def is_consistent(self) -> bool:
        return not self.conflicts()

    def is_complete(self) -> bool:
        return all(value != EMPTY for row in self._grid for value in row)

    def is_solved(self) -> bool:
        return self.is_complete() and self.is_consistent()

    def candidates(self, row: int, col: int) -> set[int]:
        """Return legal values for an empty cell."""
        if self._grid[row][col] != EMPTY:
            return {self._grid[row][col]}

        used = {
            self._grid[unit_row][unit_col]
            for unit in CELL_UNITS[(row, col)]
            for unit_row, unit_col in unit
            if self._grid[unit_row][unit_col] != EMPTY
        }
        return set(DIGITS.difference(used))

    def candidate_map(self) -> dict[Position, set[int]]:
        return {
            position: self.candidates(*position)
            for position in self.empty_positions()
        }

    def _apply_naked_singles(self) -> tuple[bool, bool]:
        candidates = self.candidate_map()
        if any(not options for options in candidates.values()):
            return False, False

        singles = [
            (position, next(iter(options)))
            for position, options in candidates.items()
            if len(options) == 1
        ]
        if not singles:
            return False, True

        for (row, col), value in singles:
            self._grid[row][col] = value
            self.stats.naked_singles += 1
        return True, self.is_consistent()

    def _apply_hidden_single(self) -> tuple[bool, bool]:
        candidates = self.candidate_map()
        if any(not options for options in candidates.values()):
            return False, False

        for unit in UNITS:
            present = {self._grid[row][col] for row, col in unit if self._grid[row][col]}
            for value in DIGITS.difference(present):
                locations = [
                    (row, col)
                    for row, col in unit
                    if self._grid[row][col] == EMPTY
                    and value in candidates[(row, col)]
                ]
                if not locations:
                    return False, False
                if len(locations) == 1:
                    row, col = locations[0]
                    self._grid[row][col] = value
                    self.stats.hidden_singles += 1
                    return True, self.is_consistent()
        return False, True

    def propagate(self) -> bool:
        """Repeatedly apply naked and hidden singles."""
        if not self.is_consistent():
            return False

        while True:
            changed, valid = self._apply_naked_singles()
            if not valid:
                return False
            if changed:
                continue

            changed, valid = self._apply_hidden_single()
            if not valid:
                return False
            if changed:
                continue
            return True

    def solve(self) -> bool:
        """Solve the board in place using propagation and MRV backtracking."""
        initial_grid = self.values()
        self.stats = SolveStats()
        if self._solve_recursive():
            return True
        self._grid = initial_grid
        return False

    def _solve_recursive(self) -> bool:
        if not self.propagate():
            return False
        if self.is_complete():
            return self.is_consistent()

        candidates = self.candidate_map()
        if any(not options for options in candidates.values()):
            return False

        position, options = min(
            candidates.items(),
            key=lambda item: (len(item[1]), item[0][0], item[0][1]),
        )
        row, col = position
        snapshot = self.values()

        for value in sorted(options):
            self.stats.guesses += 1
            self._grid[row][col] = value
            if self._solve_recursive():
                return True
            self.stats.backtracks += 1
            self._grid = [saved_row.copy() for saved_row in snapshot]
        return False

    def __str__(self) -> str:
        return "\n".join(self.rows())


def format_board(board: Board) -> str:
    """Return an easy-to-read board with box separators."""
    rows: list[str] = []
    for row_index, row in enumerate(board.values()):
        if row_index and row_index % BOX_SIZE == 0:
            rows.append("------+-------+------")
        parts = []
        for col_index, value in enumerate(row):
            if col_index and col_index % BOX_SIZE == 0:
                parts.append("|")
            parts.append(str(value) if value else ".")
        rows.append(" ".join(parts))
    return "\n".join(rows)
