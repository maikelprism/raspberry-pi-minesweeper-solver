import random

class MinesweeperAI:
    """
    A solver for Minesweeper that uses a set of logical constraints derived from
    revealed clues to infer safe cells and mines deterministically.
    """
    def __init__(self, width, height):
        """
        Initializes the Minesweeper AI.

        Args:
            width: The width of the game board.
            height: The height of the game board.
        """
        self.width = width
        self.height = height
        self.moves_made = set()
        self.safes = set()
        self.mines = set()
        # Collection of constraint equations (each relates a set of cells to a mine count)
        self.constraints = []

    def mark_mine(self, cell):
        """
        Marks a cell as a mine and updates all constraints that contain this cell.
        """
        if cell not in self.mines:
            self.mines.add(cell)
            for constraint in self.constraints:
                constraint.mark_mine(cell)
        
    def mark_safe(self, cell):
        """
        Marks a cell as safe and updates all constraints that contain this cell.
        """
        if cell not in self.safes:
            self.safes.add(cell)
            for constraint in self.constraints:
                constraint.mark_safe(cell)

    def add_constraint(self, cell, count):
        """
        Adds a new constraint derived from a revealed clue (cell, adjacent mine count).

        Args:
            cell: The (row, col) position of the revealed cell.
            count: The number of adjacent mines to the revealed cell.
        """
        self.moves_made.add(cell)
        self.mark_safe(cell)
        
        adjacent_cells = set()
        known_mine_count = 0

        # Iterate over neighbors to build the sentence
        for r_offset in [-1, 0, 1]:
            for c_offset in [-1, 0, 1]:
                if r_offset == 0 and c_offset == 0:
                    continue

                adj_cell = (cell[0] + r_offset, cell[1] + c_offset)

                if 0 <= adj_cell[0] < self.height and 0 <= adj_cell[1] < self.width:
                    if adj_cell in self.mines:
                        known_mine_count += 1
                    elif adj_cell not in self.safes:
                        adjacent_cells.add(adj_cell)

        # Add the new constraint to our set
        if adjacent_cells:
            new_constraint = Constraint(adjacent_cells, count - known_mine_count)
            if new_constraint not in self.constraints:
                self.constraints.append(new_constraint)

        # Evaluate after integrating new constraint
        self.evaluate_constraints()

    def evaluate_constraints(self):
        """
        Continuously evaluates current constraints to infer new mines and safe cells
        until no more inferences can be made.
        """
        made_inference = True
        while made_inference:
            made_inference = False
            
            # Infer safes and mines from simple sentences
            safes_to_add = set()
            mines_to_add = set()
            for constraint in self.constraints:
                if constraint.known_safes():
                    safes_to_add.update(constraint.known_safes())
                if constraint.known_mines():
                    mines_to_add.update(constraint.known_mines())

            if safes_to_add:
                for safe in safes_to_add:
                    if safe not in self.safes:
                        self.mark_safe(safe)
                        made_inference = True
            
            if mines_to_add:
                for mine in mines_to_add:
                    if mine not in self.mines:
                        self.mark_mine(mine)
                        made_inference = True

            # Remove resolved (empty) constraints
            self.constraints = [c for c in self.constraints if c.cells]

            # Infer new constraints from subsets (C2 - C1)
            constraints_copy = self.constraints[:]
            for c1 in constraints_copy:
                for c2 in constraints_copy:
                    if c1.cells == c2.cells:
                        continue
                    
                    if c1.cells.issubset(c2.cells):
                        new_cells = c2.cells - c1.cells
                        new_count = c2.count - c1.count
                        new_constraint = Constraint(new_cells, new_count)
                        
                        if new_constraint not in self.constraints:
                            self.constraints.append(new_constraint)
                            made_inference = True

                                    
    def make_safe_move(self):
        """
        Returns a safe cell to move to that has not already been moved to.

        Returns:
            A (row, col) tuple for a safe move, or None if no safe move is available.
        """
        safe_moves = self.safes - self.moves_made
        if safe_moves:
            return safe_moves.pop()
        return None

    def make_random_move(self):
        """
        Returns a random, valid move that has not yet been made or identified as a mine.
        """
        all_cells = set((r, c) for r in range(self.height) for c in range(self.width))
        possible_moves = all_cells - self.moves_made - self.mines
        if possible_moves:
            return random.choice(list(possible_moves))
        return None


class Constraint:
    """
    Represents a constraint equation of the form:
    "A set of cells contains exactly N mines."
    """
    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return isinstance(other, Constraint) and self.cells == other.cells and self.count == other.count

    def __hash__(self):
        return hash((frozenset(self.cells), self.count))

    def __repr__(self):
        return f"Constraint({self.cells}, {self.count})"

    def known_mines(self):
        """Returns all cells in the constraint if they are all mines."""
        if len(self.cells) == self.count:
            return self.cells
        return None
        
    def known_safes(self):
        """Returns all cells in the constraint if they are all safe."""
        if self.count == 0:
            return self.cells
        return None
        
    def mark_mine(self, cell):
        """Removes a cell from the constraint if it is known to be a mine."""
        if cell in self.cells:
            self.cells.remove(cell)
            self.count -= 1

    def mark_safe(self, cell):
        """Removes a cell from the constraint if it is known to be safe."""
        if cell in self.cells:
            self.cells.remove(cell)






