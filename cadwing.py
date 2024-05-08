#!/usr/bin/env python3
from FreeCADGui import Selection
import FreeCAD
from sys import path
path.append('/home/tugdual/cad/Cadwing')
from wing_from_faces import get_sections_endpoints
from wing import Wing

wing_name = "wing_example"
profil_file_path = "/home/tugdual/cad/Cadwing/hq209.dat"

doc = FreeCAD.ActiveDocument
wing_objects = doc.findObjects(Label=wing_name+"*")

for ob in wing_objects:
    try :
        doc.removeObject(ob.Name)
    except :
        pass

doc.recompute()

#Selection.addSelectionGate("SELECT Part::Feature SUBELEMENT Face")
#Selection.removeSelectionGate()
#Selection.clearSelection()
#Selection.addSelection(doc.Common,['Face3', 'Face4'])
#
selecs = Selection.getSelectionEx()
subobjects = []
for sel in selecs:
    for sub in sel.SubObjects:
        subobjects += [sub]

if len(subobjects) != 2:
    print("Please select two faces,the first face must coplanar withe the the wing first section.")

face1 = subobjects[0]
face2 = subobjects[1]

_, _, endpts = get_sections_endpoints(face1, face2, spacing=30.0, auto_spacing_coeff=1.5)

wing = Wing(doc, wing_name)
wing.load_foilprofile(profil_file_path)

names = [profil_file_path for i in range(endpts.shape[0])]

wing.add_sections(names, endpts[:,:3], endpts[:,3:] , orientation=-1)
sections = wing.make_part_sections()
wing_obj = wing.build_wing_solid(sections)
wing_obj.ViewObject.DisplayMode = "Shaded"

doc.recompute()
