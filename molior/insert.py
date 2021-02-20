import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from molior.baseclass import Molior

class Insert(Molior):
    """A profile following a horizontal 2D path"""
    def __init__(self, args = {}):
        super().__init__(args)
        self.location = [0.0, 0.0]
        self.rotation = 0
        self.space = []
        self.type = 'molior-insert'
        for arg in args:
            self.__dict__[arg] = args[arg]