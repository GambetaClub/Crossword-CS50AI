import sys
import asyncio

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def check_compatibility(self, v1, v2, x, y):
        """
        Check if two variables' values are comaptible with 
        each other (do not have any conflict in the overlaps) 
        Returns True if they are compatible. Otherwise, it returns False.
        Also, it returns True if they don't overlap.
        """
        overlap = self.crossword.overlaps[v1, v2]
        if overlap == None:
            return True
        x_letter = x[overlap[0]]
        y_letter = y[overlap[1]]
        if x_letter == y_letter:
            return True
        return False

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for variable in self.domains.keys():
            new_v_domain = []

            for value in self.domains[variable]:
                if variable.length == len(value):
                    new_v_domain.append(value)

            self.domains[variable] = new_v_domain
    

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
        overlap = self.crossword.overlaps[x,y]
        if overlap is None:
           return False
        
        trash_values = set()
        # For every single value in x's domain
        for x_value in self.domains[x]:
            # Only keep track of the overlaping letter.
            x_letter = x_value[overlap[0]]

            # Only keep the letters of the y_values at the overlaping cell.
            y_letters = [y_value[overlap[1]] for y_value in self.domains[y]]

            # Checks if the x_letter (letter at overlap cell) at least shares 
            # one letter with one of the y_values at the overlaping cell.
            if x_letter not in y_letters:
                # If not, then the value is useless and should
                # be removed from x's domain. 
                trash_values.add(x_value)
                revised = True
        
        # Removes all the useless values from x's domains
        for value in trash_values:
            self.domains[x].remove(value)

        return revised
            


    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        queue = []
        if arcs is None:
            for v1 in self.crossword.variables:
                for v2 in self.crossword.neighbors(v1):
                    queue.append((v1,v2))
        else:
            queue = arcs
            
        while len(queue) > 0:
            (x,y) = queue.pop(0)
            if self.revise(x,y):
                if len(self.domains[x]) == 0:
                    return False
                for z in self.crossword.neighbors(x):
                    if z == y:
                        continue
                    else:
                        queue.append((z,x))

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for variable in self.crossword.variables:
            if variable not in assignment:
                return False
            if not assignment[variable]:
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """

        """"This is the function that doesn't work"""
        used_values = []
        for variable in assignment:
            
            if len(assignment[variable]) != variable.length:
                return False
            if assignment[variable] in used_values:
                return False

            # Only check the variable neighbors that have a value (the ones that are in assignment)
            for neighbor in list(set(self.crossword.neighbors(variable) & assignment.keys())):
                overlap = self.crossword.overlaps[variable, neighbor]
                if overlap is None:
                    continue
                if not self.check_compatibility(variable, neighbor, assignment[variable], assignment[neighbor]):
                    return False
                  
            used_values += assignment[variable]

        return True
        

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        ordered_values = []
        return self.domains[var]


    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        values = float('inf')
        degree = float('-inf')
        candidate = None
        # Get only the variables that haven't been assigned (the ones are not in assignment)
        unassigned_variables  = list(set(self.domains) - set(assignment.keys()))
        for variable in unassigned_variables:
            if len(self.domains[variable]) < values:
                candidate = variable
                values = len(self.domains[candidate])
                degree = len(self.crossword.neighbors(candidate))
            elif len(self.domains[variable]) == values:
                if len(self.crossword.neighbors(variable)) > len(self.crossword.neighbors(candidate)):
                    candidate = variable
                    values = len(self.domains[candidate])
                    degree = len(self.crossword.neighbors(candidate))
        return candidate


    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            
            new_assignment = assignment.copy()
            new_assignment[var] = value
            if self.consistent(new_assignment):
                assignment[var] = value
                result = self.backtrack(assignment)
                if result is not None:
                    return result
        return None

def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
