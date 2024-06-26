#!/usr/bin/env python3
#
# This is the main script
#
from FreeCADGui import Selection
import FreeCAD
# FreeCAD change the python path during execution so this is needed
from sys import path
path.append('/home/tugdual/cad/Cadwing')

from chordlines import faces_to_chordlines_auto
from wing import Wing

wing_name = "wing_example"
profil_file_path = "/home/tugdual/cad/Cadwing/hq209.dat"

doc = FreeCAD.ActiveDocument

# Cleaning the precedent tries
wing_objects = doc.findObjects(Label=wing_name+"*")
for ob in wing_objects:
    doc.removeObject(ob.Name)

doc.recompute()

# if Needed you can select faces automatically
#Selection.clearSelection()
#Selection.addSelection(doc.Common,['Face3', 'Face4'])

selecs = Selection.getSelectionEx()
subobjects = []
for sel in selecs:
    for sub in sel.SubObjects:
        subobjects += [sub]

if len(subobjects) != 2:
    print("Please select two faces,the first face must coplanar withe the the wing first section.")

face1 = subobjects[0]
face2 = subobjects[1]

# Automatic spacing
_, endpts = faces_to_chordlines_auto(face1, face2, spacing=40.0, auto_spacing_coeff=1.5, min_tip_distance=0.5)

# If you need to provide the spacings yourself :
# spacing_secs = np.array([[0,30],[250,5],[350,30],[950,5]])
# _, endpts = faces_to_chordlines(face1, face2, spacing_sections=spacing_secs, min_tip_distance=0.5)


wing = Wing(doc, wing_name)
wing.load_foilprofile(profil_file_path)

# attribuates a foil shape to each sections
names = [profil_file_path for i in range(endpts.shape[0])]

wing.add_sections(names, endpts[:,:3], endpts[:,3:] , orientation=1)
sections = wing.make_spline_sections()
wing_obj, section_objs = wing.build_wing_solid(sections)


# Cosmetics
#
#Hide the sections
for sec_ob in section_objs:
    sec_ob.ViewObject.Visibility = False

# Augment rendering quality, otherwise some artefacts may appear
wing_obj.ViewObject.Deviation = 0.1

wing_obj.ViewObject.DisplayMode = "Shaded"
wing_obj.ViewObject.ShapeColor = (0.16470588743686676, 0.800000011920929, 0.7803921699523926, 0.0) #Sky-blue color
doc.recompute()
