import topologic
from topologic import Vertex, Edge, Face
from topologist.helpers import create_stl_list, el

def FacesVertical(self, faces_result):
    elements_ptr = create_stl_list(Face)
    self.Faces(elements_ptr)
    for face in elements_ptr:
        if face.IsVertical():
            faces_result.push_back(face)

def FacesHorizontal(self, faces_result):
    elements_ptr = create_stl_list(Face)
    self.Faces(elements_ptr)
    for face in elements_ptr:
        if face.IsHorizontal():
            faces_result.push_back(face)

def Elevation(self):
    lowest = 9999999.9
    vertices = create_stl_list(Vertex)
    self.Vertices(vertices)
    for vertex in vertices:
        if vertex.Z() < lowest:
            lowest = vertex.Z()
    return el(lowest)

def Height(self):
    highest = -9999999.9
    vertices = create_stl_list(Vertex)
    self.Vertices(vertices)
    for vertex in vertices:
        if vertex.Z() > highest:
            highest = vertex.Z()
    return el(highest - self.Elevation())

def EdgesTop(self, edges_result):
    """A list of horizontal edges at the highest level of this face"""
    edges = create_stl_list(Edge)
    self.Edges(edges)
    level = el(self.Elevation() + self.Height())
    for edge in edges:
        vertex_start = edge.StartVertex()
        vertex_end = edge.EndVertex()
        if el(vertex_start.Z()) == level and el(vertex_end.Z()) == level:
            edges_result.push_back(edge)

def EdgesBottom(self, edges_result):
    """A list of horizontal edges at the lowest level of this face"""
    edges = create_stl_list(Edge)
    self.Edges(edges)
    level = self.Elevation()
    for edge in edges:
        vertex_start = edge.StartVertex()
        vertex_end = edge.EndVertex()
        if el(vertex_start.Z()) == level and el(vertex_end.Z()) == level:
            edges_result.push_back(edge)

setattr(topologic.Topology, 'FacesVertical', FacesVertical)
setattr(topologic.Topology, 'FacesHorizontal', FacesHorizontal)
setattr(topologic.Topology, 'Elevation', Elevation)
setattr(topologic.Topology, 'Height', Height)
setattr(topologic.Topology, 'EdgesTop', EdgesTop)
setattr(topologic.Topology, 'EdgesBottom', EdgesBottom)
