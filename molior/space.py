import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from molior.baseclass import Molior

class Space(Molior):
    """A room or outdoor volume, as a 2D path extruded vertically"""
    def __init__(self, args = {}):
        super().__init__(args)
        self.ceiling = 0.2
        self.colour = 255
        self.floor = 0.02
        self.id = ''
        self.inner = 0.08
        self.path = []
        self.type = 'molior-space'
        self.usage = ''
        for arg in args:
            self.__dict__[arg] = args[arg]
