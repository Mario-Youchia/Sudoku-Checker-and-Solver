"""Tkinter interface for checking and solving Sudoku puzzles."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from .board import BOARD_SIZE, Board, InvalidPuzzleError
from .io import load_board


class SudokuApp:
    """Desktop interface for the Sudoku checker and solver."""

    def __init__(self, root: tk.Tk, initial_board: Board | None = None) -> None:
        self.root = root
        self.root.title("Sudoku Checker and Solver")
        self.root.resizable(False, False)

        self.entries: list[list[tk.Entry]] = []
        self.given_positions: set[tuple[int, int]] = set()
        self.status = tk.StringVar(value="Enter a puzzle or load a .sdk file.")

        self._build_layout()
        if initial_board is not None:
            self.set_board(initial_board)

    def _build_layout(self) -> None:
        outer = tk.Frame(self.root, padx=18, pady=18, bg="#f5f7fb")
        outer.pack(fill="both", expand=True)

        title = tk.Label(
            outer,
            text="Sudoku Checker and Solver",
            font=("Helvetica", 20, "bold"),
            bg="#f5f7fb",
            fg="#172033",
        )
        title.pack(pady=(0, 12))

        board_frame = tk.Frame(outer, bg="#172033", bd=0)
        board_frame.pack()

        for row in range(BOARD_SIZE):
            entry_row: list[tk.Entry] = []
            for col in range(BOARD_SIZE):
                left = 3 if col % 3 == 0 else 1
                top = 3 if row % 3 == 0 else 1
                right = 3 if col == BOARD_SIZE - 1 else 0
                bottom = 3 if row == BOARD_SIZE - 1 else 0
                cell_frame = tk.Frame(
                    board_frame,
                    bg="#172033",
                )
                cell_frame.grid(
                    row=row,
                    column=col,
                    padx=(left, right),
                    pady=(top, bottom),
                )

                entry = tk.Entry(
                    cell_frame,
                    width=2,
                    justify="center",
                    font=("Helvetica", 22, "bold"),
                    relief="flat",
                    bg="#ffffff" if (row // 3 + col // 3) % 2 == 0 else "#eef3f8",
                    fg="#172033",
                    insertbackground="#172033",
                    highlightthickness=0,
                )
                entry.pack(ipadx=7, ipady=7)
                entry.bind("<KeyRelease>", lambda event, r=row, c=col: self._limit_cell(r, c))
                entry_row.append(entry)
            self.entries.append(entry_row)

        buttons = tk.Frame(outer, bg="#f5f7fb")
        buttons.pack(pady=(14, 8))
        for text, command in [
            ("Load", self.load_dialog),
            ("Check", self.check_board),
            ("Solve", self.solve_board),
            ("Clear", self.clear_board),
        ]:
            tk.Button(
                buttons,
                text=text,
                command=command,
                width=10,
                font=("Helvetica", 11, "bold"),
                bg="#245b8a" if text == "Solve" else "#dde7f0",
                fg="#ffffff" if text == "Solve" else "#172033",
                relief="flat",
                padx=5,
                pady=7,
                cursor="hand2",
            ).pack(side="left", padx=4)

        tk.Label(
            outer,
            textvariable=self.status,
            font=("Helvetica", 10),
            bg="#f5f7fb",
            fg="#43516b",
            wraplength=460,
        ).pack(pady=(2, 0))

    def _limit_cell(self, row: int, col: int) -> None:
        entry = self.entries[row][col]
        value = entry.get().strip()
        accepted = next((character for character in reversed(value) if character in "123456789"), "")
        if value != accepted:
            entry.delete(0, tk.END)
            entry.insert(0, accepted)
        self._reset_cell_colors()

    def _board_from_entries(self) -> Board:
        rows = []
        for row in self.entries:
            rows.append("".join(entry.get().strip() or "." for entry in row))
        return Board.from_rows(rows)

    def _reset_cell_colors(self) -> None:
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                entry = self.entries[row][col]
                background = "#ffffff" if (row // 3 + col // 3) % 2 == 0 else "#eef3f8"
                entry.configure(bg=background)

    def _show_conflicts(self, conflicts: set[tuple[int, int]]) -> None:
        self._reset_cell_colors()
        for row, col in conflicts:
            self.entries[row][col].configure(bg="#ffd6d6")

    def set_board(self, board: Board) -> None:
        self.given_positions.clear()
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                entry = self.entries[row][col]
                entry.delete(0, tk.END)
                value = board.value_at(row, col)
                if value:
                    entry.insert(0, str(value))
                    self.given_positions.add((row, col))
                    entry.configure(fg="#174f78")
                else:
                    entry.configure(fg="#172033")
        self._reset_cell_colors()
        self.status.set("Puzzle loaded. Use Check or Solve.")

    def load_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="Open Sudoku puzzle",
            filetypes=[("Sudoku files", "*.sdk"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.set_board(load_board(Path(path)))
        except (OSError, InvalidPuzzleError) as error:
            messagebox.showerror("Unable to load puzzle", str(error))

    def check_board(self) -> None:
        try:
            board = self._board_from_entries()
        except InvalidPuzzleError as error:
            self.status.set(str(error))
            return

        conflicts = board.conflicts()
        self._show_conflicts(conflicts)
        if conflicts:
            self.status.set(f"Found {len(conflicts)} conflicting cells.")
        elif board.is_complete():
            self.status.set("The board is complete and valid.")
        else:
            self.status.set("No row, column, or box conflicts were found.")

    def solve_board(self) -> None:
        try:
            board = self._board_from_entries()
        except InvalidPuzzleError as error:
            self.status.set(str(error))
            return

        conflicts = board.conflicts()
        if conflicts:
            self._show_conflicts(conflicts)
            self.status.set("Resolve the highlighted conflicts before solving.")
            return

        if not board.solve():
            self.status.set("No solution exists for this puzzle.")
            return

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                entry = self.entries[row][col]
                entry.delete(0, tk.END)
                entry.insert(0, str(board.value_at(row, col)))
                entry.configure(
                    fg="#174f78" if (row, col) in self.given_positions else "#2f7d4a"
                )
        self._reset_cell_colors()
        self.status.set(
            "Solved successfully — "
            f"{board.stats.naked_singles} naked singles, "
            f"{board.stats.hidden_singles} hidden singles, "
            f"{board.stats.guesses} guesses."
        )

    def clear_board(self) -> None:
        self.given_positions.clear()
        for row in self.entries:
            for entry in row:
                entry.delete(0, tk.END)
                entry.configure(fg="#172033")
        self._reset_cell_colors()
        self.status.set("Board cleared.")


def launch(initial_board: Board | None = None) -> None:
    root = tk.Tk()
    SudokuApp(root, initial_board)
    root.mainloop()
