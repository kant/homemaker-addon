import os
import sys
import ifcopenshell.api

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from molior.baseclass import BaseClass
from molior.geometry_2d import matrix_align

run = ifcopenshell.api.run


class Extrusion(BaseClass):
    """A profile following a horizontal 2D path"""

    def __init__(self, args={}):
        super().__init__(args)
        self.closed = 0
        self.extension = 0.0
        self.path = []
        self.type = "molior-extrusion"
        for arg in args:
            self.__dict__[arg] = args[arg]
