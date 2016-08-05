from enum import Enum
import string
from collections import namedtuple
from types import MappingProxyType

SYMBOLS = tuple(string.ascii_letters + string.digits + '_') + ('',)

class Move(Enum):
    Stay = 0
    Right = 1
    Left = -1

class TuringMachine(object):

    # For reporting the state of the Turing Machine after each step in computation
    TMReport = namedtuple("TMReport", ['state', 'head', 'tape'])

    # For reporting what was done during the last steo of the computation
    TMActionReport = namedtuple("TMActionReport", ['cell_written', 'symbol_written', 'move'])

    def __init__(self, tape, table):

        # Raises a Value Error if the instruction table is invalid
        self._validate_table(table)

        self._tape = Tape(tape)
        self._table = table
        self._state = 0
        self._head = 0

        # Flag indicates that the TuringMachine is in its starting state
        self._started = False
    
    def __next__(self):
        """Complete the next stage in computation, based on turing machine state and symbol under the
        read head. Using __next__ makes the TuringMachine instance an iterable, meaning that it can be used
        with next() or iterated over in a for-loop."""
        # On the first pass, just report the starting state of the TM
        if self._started: # If it isn't the first pass
            try:
                # Just for readability
                current_state = self._state
                symbol_under_head = self._tape[self._head]

                # Get transition information
                symbol_to_print, move, next_state = self._table[current_state, symbol_under_head]

            # If no instruction is found for the current state/symbol, halt the turing machine
            except KeyError:
                raise StopIteration

            # Update state
            self._state = next_state

            # Print symbol (printing of empty string results in deletion of cell contents)
            self._tape[self._head] = symbol_to_print

            # Move head
            self._head += move.value

        # If this was the first pass, update flag so that
        #   computations are carried out next time.
        # Put placeholder values in variables needed for reports.
        else:
            symbol_to_print = move = None
            self._started = True

        # Report the results of the last computation
        resulting_state = TuringMachine.TMReport(self._state, self._head, self.tape)

        action_report = TuringMachine.TMActionReport(self.head - move.value if symbol_to_print else None,
                                                     symbol_to_print or None,
                                                     move)

        return resulting_state, action_report

    def __iter__(self):
        return self

    def _validate_table(self, table):
        """Validates an instruction table"""
        for key, val in table.items():
            state1, symbol = key
            symbol_to_print, move, state2 = val
            
            # The input symbol for an instruction must be None or be in the SYMBOLS alphabet
            if str(symbol) not in SYMBOLS and symbol != None:
                raise ValueError("Symbol must be convertible to an alphanumeric or underscore character, or None")

            # The output symbol for an instruction must be in the alphabet
            # (including the empty string, which means nothing will be printed)
            if str(symbol_to_print) not in SYMBOLS:
                raise ValueError("Symbol must be convertible to an alphanumeric or underscore character")

            # Move must be one of the Move enumerator options or equivalent integers
            if not isinstance(move, Move) and move not in (-1, 0, 1):
                raise ValueError("Invalid move")

    # table, tape, state and head are read-only

    @property
    def table(self):
        """Returns a read-only proxy or 'view' of the instruction table."""
        return MappingProxyType(self._table)

    @property
    def tape(self):
        """Returns a read-only proxy or 'view' of the tape.
        It provides a dynamic view of the tape, which means that 
        when the tape changes, the view reflects these changes."""
        return self._tape.view()

    @property
    def state(self):
        return self._state

    @property
    def head(self):
        return self._head

class Tape(object):
    """A Tape object is an infinite sequence of cells in two directions. Negative indices do not
    count from the end of the sequence, as with lists, but indicate a place to the 'left' of
    the 0th element."""

    def __init__(self, tapelist):
        """The tapelist should be an 'enumerated', iterator or enumerate object of 
        the pairs of the form (cell number, value), where value is or converts to a 
        single character string. Alternatively, tapelist may itself be a string or Alternatively
        other sequence of single characters, where each character represents one cell."""

        # Validation and conversion of tapelist
        try:
            # Try to interpret tapelist as an list of tuples of the form (cell number, value)
            # Empty cells are not explicitly stored.
            tape = dict( ((cell_n, str(val)) for (cell_n, val) in tapelist if val != None) )
        except (TypeError, ValueError):
            # If that fails, try to interpret tapelist as a sequence of single characters
            tape = dict(enumerate(str(a) for a in tapelist))

        # Check that the cells only contain single character values
        # from the SYMBOLS alphabet
        for cell_n, val in tape.items():
            if len(val) > 1 or val not in SYMBOLS:
                raise ValueError("Invalid tape description")

        # Having been validated, store the tape,
        self._tape = tape

        # Since empty cells are not explicitly stored, it is necessary 
        # to keep track of the indices of the left-most and right-most
        # non-empty cells
        self._minIndex = min(n for n in self._tape.keys())
        self._maxIndex = max(n for n in self._tape.keys())

        # Store a TapeView of self, to be returned by view() method
        self._view = Tape.TapeView(self)

    def __getitem__(self, key):
        """Accept indexing, for integer indices only. Return None if cell empty."""
        
        if type(key) != int: raise TypeError("list indices must be integers, not %s" % type(key).__name__)
        
        return self._tape.get(key, None)

    def __setitem__(self, key, value):
        """Accept index assignment, for integer indices only."""
        
        if type(key) != int: raise TypeError("list indices must be integers, not %s" % type(key).__name__)
        
        # Allow 'rubbing out' of cells to make them empty...
        if value == '':
            if key in self._tape:
                del self._tape[key]
        # ... and normal writing of cells.
        else:
            self._tape[key] = value

        # Update record of rightmost and leftmost non-blank cells.
        self._minIndex = min(n for n in self._tape.keys())
        self._maxIndex = max(n for n in self._tape.keys())

    def __iter__(self):
        """Allow iteration over the cells of the tape."""
        for i in range(self._minIndex, self._maxIndex + 1):
            yield i, self[i]

    def __str__(self):
        return ''.join(str(item[1]) if item[1] != None else '#' for item in self)

    def __repr__(self):
        return 'Tape([%s])' % ', '.join(str(a) for a in self._tape.items())

    def view(self):
        return self._view

    class TapeView(object):
        """Provides a read-only proxy or 'view' of a Tape instance.
        It provides a dynamic view of the Tape instance, which means that 
        when the tape changes, the view reflects these changes."""

        def __init__(self, tape):
            self._tape = tape

        def __getitem__(self, key):
            return self._tape[key]

        def __iter__(self):
            return iter(self._tape)

        def __repr__(self):
            return "<TapeView of 0x%x: %s>" % (id(self._tape), str(self._tape))

        def __str__(self):
            return str(self._tape)

if __name__ == '__main__': 
    
    instructions = {
        (0, '0'): ('1', Move.Right, 0),
        (0, '1'): ('0', Move.Right, 0),
        (0, None): ('', Move.Right, 1),
        (1, None): ('1', Move.Stay, 2)
    }

    m = TuringMachine(list('0110100'), instructions)
    for x in m:
        print(x)