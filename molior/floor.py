import os
import sys
import ifcopenshell.api

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from molior.baseclass import BaseClass
from molior.geometry import matrix_align

run = ifcopenshell.api.run


class Floor(BaseClass):
    """A floor filling a room or space"""

    def __init__(self, args={}):
        super().__init__(args)
        self.below = 0.2
        self.id = ""
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
        entity = run(
            "root.create_entity",
            self.file,
            ifc_class=self.ifc,
            name=self.name,
        )

        element_types = {}
        for element_type in self.file.by_type(self.ifc_class):
            element_types[element_type.Name] = element_type
        if self.name in element_types:
            myelement_type = element_types[self.name]
        else:
            # we need to create a new Type
            myelement_type = run(
                "root.create_entity",
                self.file,
                ifc_class=self.ifc_class,
                name=self.name,
                predefined_type=self.predefined_type,
            )
            run(
                "project.assign_declaration",
                self.file,
                definition=myelement_type,
                relating_context=self.file.by_type("IfcProject")[0],
            )
            run(
                "material.assign_material",
                self.file,
                product=myelement_type,
                type="IfcMaterialLayerSet",
            )

            mylayerset = ifcopenshell.util.element.get_material(myelement_type)
            for mylayer in self.layerset:
                layer = run(
                    "material.add_layer",
                    self.file,
                    layer_set=mylayerset,
                    material=self.file.get_material_by_name(self.context, mylayer[1]),
                )
                layer.LayerThickness = mylayer[0]

        run(
            "type.assign_type",
            self.file,
            related_object=entity,
            relating_type=myelement_type,
        )

        # Usage isn't created until after type.assign_type
        mylayerset = ifcopenshell.util.element.get_material(myelement_type)
        for inverse in self.file.get_inverse(mylayerset):
            if inverse.is_a("IfcMaterialLayerSetUsage"):
                inverse.OffsetFromReferenceLine = 0.0 - self.below

        self.file.assign_storey_byindex(entity, self.level)
        shape = self.file.createIfcShapeRepresentation(
            self.context,
            "Body",
            "SweptSolid",
            [
                self.file.createExtrudedAreaSolid(
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
