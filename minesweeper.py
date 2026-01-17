import random
from verify import MinesweeperAI


class Cell:
    """
    Represents a single cell on the Minesweeper board.
    """
    def __init__(self, row, col):
        """
        Initializes a Cell.

        Args:
            row: The row position of the cell.
            col: The column position of the cell.
        """
        self.row = row
        self.col = col
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.adjacent_mines = 0

    def __repr__(self):
        return f"Cell({self.row}, {self.col}, Mine: {self.is_mine}, Revealed: {self.is_revealed})"


class CellSelector:
    """
    Manages the currently selected cell on the board.
    """
    def __init__(self, height, width):
        """
        Initializes the CellSelector.

        Args:
            height: The height of the board.
            width: The width of the board.
        """
        self.height = height
        self.width = width
        self.selected_pos = (0, 0)  # (row, col)

    def move(self, d_row, d_col):
        """
        Moves the selector by the given delta.

        Args:
            d_row: The change in row.
            d_col: The change in column.
        """
        new_row = self.selected_pos[0] + d_row
        new_col = self.selected_pos[1] + d_col

        # Clamp the values to be within the board boundaries
        self.selected_pos = (
            max(0, min(new_row, self.height - 1)),
            max(0, min(new_col, self.width - 1))
        )


class Minesweeper:
    """
    Represents the core logic of the Minesweeper game.
    """
    def __init__(self, height, width, num_mines):
        """
        Initializes the Minesweeper game.

        Args:
            height: The height of the board.
            width: The width of the board.
            num_mines: The number of mines to place on the board.
        """
        self.height = height
        self.width = width
        self.num_mines = num_mines
        self.cells = []            # 2D list of Cell objects
        self.mines = set()         # Set of (row, col) mine positions for O(1) lookup
        self.selector = CellSelector(height, width)
        self.is_game_over = False
        self.is_win = False
        self.first_safe_move = None  # Seed cell for AI solvability verification
        self.revealed_safe_cells = 0  # Count of revealed non-mine cells

    def init(self):
        """
        Initializes a new game by generating boards until a solvable one is found.
        """
        # Keep generating new boards until the AI confirms solvability

        attempts = 0
        max_attempts = 100000  # Prevent infinite loops in extreme cases

        while attempts < max_attempts:
            print(f"Board generation attempt {attempts + 1}")
            self._generate_board()
            self._find_first_safe_move()
            attempts += 1
            if self._is_board_solvable():
                print("Solvable board generated.")
                break
            # Otherwise, try again

    def _generate_board(self):
        """
        Creates cells, places mines randomly, and calculates adjacent mine counts.
        """
        # Create cells
        self.cells = [[Cell(row_idx, col_idx) for col_idx in range(self.width)] for row_idx in range(self.height)]
        self.mines.clear()
        self.revealed_safe_cells = 0

        # Place mines
        mines_to_place = self.num_mines
        while mines_to_place > 0:
            row_idx = random.randint(0, self.height - 1)
            col_idx = random.randint(0, self.width - 1)

            cell = self.cells[row_idx][col_idx]
            if not cell.is_mine:
                cell.is_mine = True
                self.mines.add((row_idx, col_idx))
                mines_to_place -= 1

        # Calculate adjacent mines for each cell
        for row_idx in range(self.height):
            for col_idx in range(self.width):
                cell = self.cells[row_idx][col_idx]
                if not cell.is_mine:
                    cell.adjacent_mines = sum(
                        1
                        for neighbor_row in range(row_idx - 1, row_idx + 2)
                        for neighbor_col in range(col_idx - 1, col_idx + 2)
                        if (neighbor_row, neighbor_col) in self.mines and (neighbor_row, neighbor_col) != (row_idx, col_idx)
                    )

    def _find_first_safe_move(self):
        """Select a starting safe cell preferring zero-adjacent-mine cells.

        Strategy:
        1. Gather all non-mine cells with adjacent_mines == 0.
        2. If any exist, choose one randomly (adds variation, all equivalent informationally).
        3. Otherwise, fall back to any non-mine cell (original behavior) so the game can proceed.
        """
        zero_adj = []
        fallback = None
        for row_idx in range(self.height):
            for col_idx in range(self.width):
                cell = self.cells[row_idx][col_idx]
                if not cell.is_mine:
                    if fallback is None:
                        fallback = (row_idx, col_idx)
                    if cell.adjacent_mines == 0:
                        zero_adj.append((row_idx, col_idx))
        if zero_adj:
            self.first_safe_move = random.choice(zero_adj)
        else:
            self.first_safe_move = fallback

    def reveal_cell(self, row, col):
        """
        Reveals the cell at the given position. If the cell has no adjacent
        mines, it recursively reveals its neighbors.
        """
        cell = self.cells[row][col]
        if cell.is_revealed or cell.is_flagged:
            return

        cell.is_revealed = True

        if cell.is_mine:
            self.is_game_over = True
        else:
            # Increment when revealing a safe cell
            self.revealed_safe_cells += 1
            if cell.adjacent_mines == 0:
                # Reveal neighboring cells if there are no adjacent mines
                for neighbor_row in range(row - 1, row + 2):
                    for neighbor_col in range(col - 1, col + 2):
                        if 0 <= neighbor_row < self.height and 0 <= neighbor_col < self.width and not self.cells[neighbor_row][neighbor_col].is_revealed:
                            self.reveal_cell(neighbor_row, neighbor_col)
        
        if not self.is_game_over:
            self._check_win_condition()

    def _check_win_condition(self):
        """
        Checks if the player has won the game.
        The game is won if all non-mine cells are revealed.
        """
        if self.revealed_safe_cells == (self.width * self.height) - self.num_mines:
            self.is_game_over = True
            self.is_win = True

    def flag_cell(self, row, col):
        """
        Flags or unflags the cell at the given position.

        Args:
            row: The row of the cell to flag or unflag.
            col: The column of the cell to flag or unflag.
        """
        cell = self.cells[row][col]
        if not cell.is_revealed:
            cell.is_flagged = not cell.is_flagged

    def _is_board_solvable(self):
        """
        Uses the AI solver to check if the current board configuration is solvable
        without guessing.

        Returns:
            True if the board is solvable, False otherwise.
        """
        # The AI needs to know the board dimensions
        ai = MinesweeperAI(width=self.width, height=self.height)

        if not self.first_safe_move:
            return False

        # The AI needs to know about the first safe move
        first_cell = self.cells[self.first_safe_move[0]][self.first_safe_move[1]]
        ai.add_constraint(self.first_safe_move, first_cell.adjacent_mines)
        ai.moves_made.add(self.first_safe_move)

        # Keep making safe moves until there are no more certainties
        while True:
            made_move = False
            safe_moves = ai.safes - ai.moves_made
            if not safe_moves:
                break  # No more known safe moves

            for safe_move in safe_moves:
                ai.moves_made.add(safe_move)
                made_move = True
                
                # Get the cell and its adjacent mine count
                cell = self.cells[safe_move[0]][safe_move[1]]
                ai.add_constraint(safe_move, cell.adjacent_mines)
            
            if not made_move:
                break

        # If all non-mine cells are revealed, the board is solvable
        revealed_count = len(ai.moves_made)
        total_safe_cells = self.width * self.height - self.num_mines
        return revealed_count == total_safe_cells

    def _get_neighbors(self, cell):
        """
        Gets all valid neighboring cells for a given cell.

        Args:
            cell: The cell to get neighbors for.

        Returns:
            A list of neighboring cell objects.
        """
        neighbors = []
        for neighbor_row in range(cell.row - 1, cell.row + 2):
            for neighbor_col in range(cell.col - 1, cell.col + 2):
                if (neighbor_row, neighbor_col) != (cell.row, cell.col) and 0 <= neighbor_row < self.height and 0 <= neighbor_col < self.width:
                    neighbors.append(self.cells[neighbor_row][neighbor_col])
        return neighbors
