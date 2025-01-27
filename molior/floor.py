import ifcopenshell.api

from topologic import Vertex, Face, Cell
from topologist.helpers import create_stl_list

from molior.baseclass import TraceClass
from molior.geometry import matrix_align, map_to_2d
from molior.ifc import (
    createExtrudedAreaSolid,
    createCurveBoundedPlane,
    createFaceSurface,
    assign_storey_byindex,
    get_material_by_name,
)

run = ifcopenshell.api.run


class Floor(TraceClass):
    """A floor filling a room or space"""

    def __init__(self, args={}):
        super().__init__(args)
        self.below = 0.2
        self.ifc = "IfcSlab"
        self.ifc_class = "IfcSlabType"
        self.predefined_type = "FLOOR"
        self.layerset = [[0.2, "Concrete"], [0.02, "Screed"]]
        self.path = []
        self.type = "molior-floor"
        for arg in args:
            self.__dict__[arg] = args[arg]
        # FIXME implement not_if_stair_below
        self.thickness = 0.0
        for layer in self.layerset:
            self.thickness += layer[0]

    def execute(self):
        """Generate some ifc"""
        for item in self.file.by_type("IfcGeometricRepresentationSubContext"):
            if item.ContextIdentifier == "Reference":
                reference_context = item
            if item.ContextIdentifier == "Body":
                body_context = item
        entity = run(
            "root.create_entity",
            self.file,
            ifc_class=self.ifc,
            name=self.name,
        )

        myelement_type = self.get_element_type()
        run(
            "type.assign_type",
            self.file,
            related_object=entity,
            relating_type=myelement_type,
        )
        self.add_psets(myelement_type)

        string_coor_start = next(iter(self.chain.graph))
        cell = self.chain.graph[string_coor_start][1][3]
        if cell.__class__ == Cell:
            topology_index = cell.Get("index")
            self.add_pset(entity, "EPset_Topology", {"CellIndex": str(topology_index)})
            faces_bottom = create_stl_list(Face)
            cell.FacesBottom(faces_bottom)
            faces_bottom_indices = [
                str(face.Get("index")) for face in list(faces_bottom)
            ]
            self.add_pset(
                entity,
                "EPset_Topology",
                {"FaceIndices": " ".join(faces_bottom_indices)},
            )
            for face in list(faces_bottom):
                vertices_perimeter = create_stl_list(Vertex)
                face.VerticesPerimeter(vertices_perimeter)
                vertices = [[v.X(), v.Y(), v.Z()] for v in vertices_perimeter]
                normal = face.Normal()
                # need this for boundaries
                nodes_2d, matrix, normal_x = map_to_2d(vertices, normal)
                # need this for structure
                face_surface = createFaceSurface(self.file, vertices, normal)

                # generate structural surfaces
                structural_surface = run(
                    "root.create_entity",
                    self.file,
                    ifc_class="IfcStructuralSurfaceMember",
                    name=self.name,
                )
                self.add_topology_pset(structural_surface, face, *face.CellsOrdered())
                structural_surface.PredefinedType = "SHELL"
                structural_surface.Thickness = self.thickness
                run(
                    "structural.assign_structural_analysis_model",
                    self.file,
                    product=structural_surface,
                    structural_analysis_model=self.file.by_type(
                        "IfcStructuralAnalysisModel"
                    )[0],
                )
                run(
                    "geometry.assign_representation",
                    self.file,
                    product=structural_surface,
                    representation=self.file.createIfcTopologyRepresentation(
                        reference_context,
                        "Reference",
                        "Face",
                        [face_surface],
                    ),
                )
                run(
                    "material.assign_material",
                    self.file,
                    product=structural_surface,
                    material=get_material_by_name(
                        self.file, reference_context, "Concrete"
                    ),
                )

                # generate space boundaries
                curve_bounded_plane = createCurveBoundedPlane(
                    self.file, nodes_2d, matrix
                )
                for cell in face.CellsOrdered():
                    if cell == None:
                        continue
                    boundary = run(
                        "root.create_entity",
                        self.file,
                        ifc_class="IfcRelSpaceBoundary2ndLevel",
                    )
                    boundary.PhysicalOrVirtualBoundary = "PHYSICAL"
                    if face.IsInternal():
                        boundary.InternalOrExternalBoundary = "INTERNAL"
                    else:
                        boundary.InternalOrExternalBoundary = "EXTERNAL"
                    boundary.RelatedBuildingElement = entity
                    boundary.ConnectionGeometry = (
                        self.file.createIfcConnectionSurfaceGeometry(
                            curve_bounded_plane
                        )
                    )

                    cell_index = cell.Get("index")
                    if not cell_index == None:
                        # can't assign psets to an IfcRelationship, use Description instead
                        boundary.Description = "CellIndex " + str(cell_index)

        # Usage isn't created until after type.assign_type
        mylayerset = ifcopenshell.util.element.get_material(myelement_type)
        for inverse in self.file.get_inverse(mylayerset):
            if inverse.is_a("IfcMaterialLayerSetUsage"):
                inverse.OffsetFromReferenceLine = 0.0 - self.below

        assign_storey_byindex(self.file, entity, self.level)
        shape = self.file.createIfcShapeRepresentation(
            body_context,
            "Body",
            "SweptSolid",
            [
                createExtrudedAreaSolid(
                    self.file,
                    [self.corner_in(index) for index in range(len(self.path))],
                    self.thickness,
                )
            ],
        )
        run(
            "geometry.assign_representation",
            self.file,
            product=entity,
            representation=shape,
        )
        run(
            "geometry.edit_object_placement",
            self.file,
            product=entity,
            matrix=matrix_align(
                [0.0, 0.0, self.elevation - self.below], [1.0, 0.0, 0.0]
            ),
        )
