#!/usr/bin/python3

import os
import sys
import unittest
import ifcopenshell.api

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import molior.ifc
from molior.ifc import (
    create_site,
    create_building,
    create_storeys,
    create_extruded_area_solid,
    assign_representation_fromDXF,
    assign_storey_byindex,
)
from molior.geometry import matrix_align

run = ifcopenshell.api.run


class Tests(unittest.TestCase):
    def setUp(self):
        ifc = molior.ifc.init(name="My Project")
        for item in ifc.by_type("IfcGeometricRepresentationSubContext"):
            if item.ContextIdentifier == "Body":
                body_context = item

        project = ifc.by_type("IfcProject")[0]
        site = create_site(ifc, project, "My Site")
        building = create_building(ifc, site, "My Building")
        create_storeys(ifc, building, {0.0: 0})

        # create a window
        myproduct = run(
            "root.create_entity",
            ifc,
            ifc_class="IfcWindow",
            name="My Window",
        )
        # window needs some attributes
        run(
            "attribute.edit_attributes",
            ifc,
            product=myproduct,
            attributes={"OverallHeight": 2.545, "OverallWidth": 5.0},
        )
        # place the window in space
        run(
            "geometry.edit_object_placement",
            ifc,
            product=myproduct,
            matrix=matrix_align([11.0, 0.0, 3.0], [11.0, 2.0, 0.0]),
        )
        # assign the window to a storey
        assign_storey_byindex(ifc, myproduct, 0)

        # load geometry from a DXF file and assign to the window
        assign_representation_fromDXF(
            ifc, body_context, myproduct, "default", "molior/style/share/shopfront.dxf"
        )

        # create a wall
        mywall = run("root.create_entity", ifc, ifc_class="IfcWall", name="My Wall")
        # give the wall a Body representation
        run(
            "geometry.assign_representation",
            ifc,
            product=mywall,
            representation=ifc.createIfcShapeRepresentation(
                body_context,
                "Body",
                "SweptSolid",
                [
                    create_extruded_area_solid(
                        ifc,
                        [[0.0, -0.25], [12.0, -0.25], [12.0, 0.08], [0.0, 0.08]],
                        4.0,
                    )
                ],
            ),
        )
        # place the wall in space
        run(
            "geometry.edit_object_placement",
            ifc,
            product=mywall,
            matrix=matrix_align([11.0, -0.5, 3.0], [11.0, 2.0, 0.0]),
        )
        # assign the wall to a storey
        assign_storey_byindex(ifc, mywall, 0)

        # create an opening
        myopening = run(
            "root.create_entity", ifc, ifc_class="IfcOpeningElement", name="My Opening"
        )
        run(
            "attribute.edit_attributes",
            ifc,
            product=myopening,
            attributes={"PredefinedType": "OPENING"},
        )
        # give the opening a Body representation
        run(
            "geometry.assign_representation",
            ifc,
            product=myopening,
            representation=ifc.createIfcShapeRepresentation(
                body_context,
                "Body",
                "SweptSolid",
                [
                    create_extruded_area_solid(
                        ifc, [[0.5, -1.0], [5.5, -1.0], [5.5, 1.0], [0.5, 1.0]], 2.545
                    )
                ],
            ),
        )
        # place the opening where the wall is
        run(
            "geometry.edit_object_placement",
            ifc,
            product=myopening,
            matrix=matrix_align([11.0, -0.5, 3.0], [11.0, 2.0, 0.0]),
        )
        # use the opening to cut the wall, no need to assign a storey
        run("void.add_opening", ifc, opening=myopening, element=mywall)
        # associate the opening with our window
        run("void.add_filling", ifc, opening=myopening, element=myproduct)

        # create another window
        myproduct = run(
            "root.create_entity",
            ifc,
            ifc_class="IfcWindow",
            name="Another Window",
        )
        # window needs some attributes
        run(
            "attribute.edit_attributes",
            ifc,
            product=myproduct,
            attributes={"OverallHeight": 2.545, "OverallWidth": 5.0},
        )
        # place the window in space
        run(
            "geometry.edit_object_placement",
            ifc,
            product=myproduct,
            matrix=matrix_align([11.0, 6.0, 3.0], [11.0, 9.0, 0.0]),
        )
        # assign the window to a storey
        assign_storey_byindex(ifc, myproduct, 0)

        # shopfront.dxf is already imported and mapped
        assign_representation_fromDXF(
            ifc, body_context, myproduct, "default", "molior/style/share/shopfront.dxf"
        )

        # create an opening
        myopening = run(
            "root.create_entity",
            ifc,
            ifc_class="IfcOpeningElement",
            name="Another Opening",
        )
        run(
            "attribute.edit_attributes",
            ifc,
            product=myopening,
            attributes={"PredefinedType": "OPENING"},
        )
        # give the opening a Body representation
        run(
            "geometry.assign_representation",
            ifc,
            product=myopening,
            representation=ifc.createIfcShapeRepresentation(
                body_context,
                "Body",
                "SweptSolid",
                [
                    create_extruded_area_solid(
                        ifc, [[0.5, -1.0], [5.5, -1.0], [5.5, 1.0], [0.5, 1.0]], 2.545
                    )
                ],
            ),
        )
        # place the opening where the wall is
        run(
            "geometry.edit_object_placement",
            ifc,
            product=myopening,
            matrix=matrix_align([11.0, 5.5, 3.0], [11.0, 9.0, 0.0]),
        )
        # use the opening to cut the wall, no need to assign a storey
        run("void.add_opening", ifc, opening=myopening, element=mywall)
        # associate the opening with our window
        run("void.add_filling", ifc, opening=myopening, element=myproduct)

        ifc.write("_test.ifc")

    def test_noop(self):
        pass


if __name__ == "__main__":
    unittest.main()
