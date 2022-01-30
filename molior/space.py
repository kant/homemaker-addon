import ifcopenshell.api
import numpy

from molior.baseclass import TraceClass
from molior.geometry import matrix_align
from molior.ifc import (
    create_extruded_area_solid,
    create_tessellation_from_mesh,
    assign_storey_byindex,
)

run = ifcopenshell.api.run


class Space(TraceClass):
    """A room or outdoor volume, as a 2D path extruded vertically"""

    def __init__(self, args=None):
        if args is None:
            args = {}
        super().__init__(args)
        self.ceiling = 0.2
        self.floor = 0.02
        self.ifc = "IfcSpace"
        self.inner = 0.08
        self.path = []
        self.type = "molior-space"
        self.usage = ""
        for arg in args:
            self.__dict__[arg] = args[arg]
        self.usage = self.name

    def execute(self):
        """Generate some ifc"""
        for item in self.file.by_type("IfcGeometricRepresentationSubContext"):
            if item.ContextIdentifier == "Body":
                body_context = item
        # the cell is the first cell attached to any edge in the chain
        cell = self.chain.graph[next(iter(self.chain.graph))][1]["back_cell"]

        element = run(
            "root.create_entity",
            self.file,
            ifc_class=self.ifc,
            name=self.usage + "/" + str(cell.Get("index")),
        )

        try:
            is_external = cell.IsOutside()
            crinkliness = int(cell.Crinkliness(self.cellcomplex) * 10) / 10
        except:
            is_external = False
            crinkliness = 1.0
        separation = cell.Get("separation")
        if separation != None:
            separation = float(separation)

        self.add_pset(
            element,
            "EPset_Pattern",
            {"Crinkliness": crinkliness, "Separation": separation},
        )
        topology_index = cell.Get("index")
        if not topology_index == None:
            self.add_pset(element, "EPset_Topology", {"CellIndex": str(topology_index)})

        # FIXME should create IfcSpaceType for this
        self.add_psets(element)

        assign_storey_byindex(self.file, element, self.building, self.level)

        if not self.do_representation:
            return
        # simple extruded representation
        representation = create_extruded_area_solid(
            self.file,
            [self.corner_in(index) for index in range(len(self.path))],
            self.height - self.ceiling,
        )
        representationtype = "SweptSolid"

        # clip if original cell has non-horizontal ceiling
        faces_ptr = []
        cell.FacesInclined(faces_ptr)
        if len(faces_ptr) > 0:
            vertices, faces = cell.Mesh()
            vertices = [
                [v[0], v[1], v[2] - self.elevation - self.floor] for v in vertices
            ]
            tessellation = create_tessellation_from_mesh(self.file, vertices, faces)
            representation = self.file.createIfcBooleanResult(
                "INTERSECTION", representation, tessellation
            )
            representationtype = "CSG"

        shape = self.file.createIfcShapeRepresentation(
            body_context,
            body_context.ContextIdentifier,
            representationtype,
            [representation],
        )

        if not is_external:
            red = numpy.clip(1.0 - crinkliness, 0.0, 1.0)
            green = numpy.clip(crinkliness, 0.0, 1.0)
            blue = numpy.clip(crinkliness - 1.0, 0.0, 1.0)
            style = run(
                "style.add_style", self.file, name="Crinkliness " + str(crinkliness)
            )
            run(
                "style.add_surface_style",
                self.file,
                style=style,
                attributes={
                    "SurfaceColour": {
                        "Name": None,
                        "Red": red,
                        "Green": green,
                        "Blue": blue,
                    },
                    "DiffuseColour": {
                        "Name": None,
                        "Red": red,
                        "Green": green,
                        "Blue": blue,
                    },
                    "Transparency": 0.5,
                    "ReflectanceMethod": "PLASTIC",
                },
            )
            # FIXME report 159 LIGHT ON TWO SIDES: custom psets? STDERR?
        else:
            style = run("style.add_style", self.file, name="Outdoor Space")
            run(
                "style.add_surface_style",
                self.file,
                style=style,
                attributes={
                    "SurfaceColour": {
                        "Name": None,
                        "Red": 1.0,
                        "Green": 1.0,
                        "Blue": 1.0,
                    },
                    "DiffuseColour": {
                        "Name": None,
                        "Red": 1.0,
                        "Green": 1.0,
                        "Blue": 1.0,
                    },
                    "Transparency": 0.9,
                    "ReflectanceMethod": "PLASTIC",
                },
            )
        run(
            "style.assign_representation_styles",
            self.file,
            shape_representation=shape,
            styles=[style],
        )

        run(
            "geometry.assign_representation",
            self.file,
            product=element,
            representation=shape,
        )
        run(
            "geometry.edit_object_placement",
            self.file,
            product=element,
            matrix=matrix_align(
                [0.0, 0.0, self.elevation + self.floor], [1.0, 0.0, 0.0]
            ),
        )
