#!/usr/bin/env python3
#
# This module contain functions to determine the position of
# the wing's leading and trailing edges from a face in freecad.
#
#
from FreeCADGui import Selection
from FreeCAD import Vector
import FreeCAD
import Draft
import Part
import numpy as np
from wing import Wing


def plane_slice(plane1, face2, space, min_tip_distance, height):
    """ Generate a new plane (plane2) *space* away from plane1
    and locally perpendicular to face2.
    Then computes the intersection line between plane2 and
    face2 in order to get the chordline.
    """

    length = height

    EndOfFace = False
    # Get the center of intersection between the two surfaces
    line = face2.section(plane1)
    center = line.CenterOfGravity

    # center = plane1.CenterOfMass
    uv = plane1.Surface.parameter(center)  # get the parameter u,v

    plane1_normal = plane1.normalAt(uv[0], uv[1])
    plane1_normal = np.array([plane1_normal.x, plane1_normal.y, plane1_normal.z])

    # Move the center forward for the next plane section
    center = np.array([center.x,center.y,center.z])
    center = center - space*plane1_normal

    # find the normal of the shape's face at the new point
    uv = face2.Surface.parameter(Vector(*center))  # get the parameter u,v
    face2_normal = face2.normalAt(uv[0], uv[1])
    face2_normal = np.array([face2_normal.x, face2_normal.y, face2_normal.z])

    # Move the center of the next plane on the surface
    center = face2.Surface.value(uv[0],uv[1])
    center = np.array([center.x,center.y,center.z])

    if space != 0:
        # making the next section plane's normal perpendicular to the face's normal
        new_normal = plane1_normal-face2_normal*np.dot(face2_normal, plane1_normal)
        new_normal /= np.linalg.norm(new_normal)
    else :
        new_normal = plane1_normal

    xaxis = np.cross(face2_normal, new_normal)
    xaxis /= np.linalg.norm(xaxis)
    zaxis = face2_normal
    zaxis = np.cross(xaxis,new_normal)
    zaxis /= np.linalg.norm(zaxis)

    if not face2.isInside(Vector(*center),0.0000001,True):
        doc = FreeCAD.ActiveDocument
        pt = doc.addObject("Part::Vertex", "Point_tip")
        pt.X = center[0]
        pt.Y = center[1]
        pt.Z = center[2]
        dist = space
        for edge in face2.Edges:
            dist_tmp, pts ,_ = edge.distToShape(pt.Shape)
            if dist_tmp < dist :
                dist = dist_tmp
                center = np.array([pts[0][0].x, pts[0][0].y, pts[0][0].z])
                center += min_tip_distance*plane1_normal
        EndOfFace = True
        doc.removeObject(pt.Name)

    plane_loc = center
    plane_loc = plane_loc + length/2*xaxis + height/2*zaxis
    plane2 = Part.makePlane(height,length,Vector(*plane_loc), Vector(*new_normal), Vector(*(face2_normal)))
    segm = face2.section(plane2)

    # Orient the segment correctly
    segm_vert = segm.Vertexes
    segm_start = np.array([segm_vert[0].X,segm_vert[0].Y,segm_vert[0].Z])
    segm_end = np.array([segm_vert[1].X,segm_vert[1].Y,segm_vert[1].Z])
    segm_vect = segm_end - segm_start
    if np.dot(xaxis, segm_vect) < 0 :
        segm_start_tmp = segm_start
        segm_start = segm_end
        segm_end = segm_start_tmp

    return plane2, segm, np.hstack((segm_start, segm_end)), EndOfFace

def faces_to_chordlines(face1, face2, spacing, auto_spacing_coeff = 1.0, min_tip_distance=1):
    """ return a set of chordlines along the wing span. """

    height = face2.BoundBox.DiagonalLength*0.2

    last_segms_len = np.zeros(3)
    spacing_auto = spacing
    last_spacings = np.full(2,spacing_auto)
    segments = []
    lines = []
    planes = []
    # A plane is also a face
    face1, line, segm, eof = plane_slice(face1, face2, 0.0, min_tip_distance, height)
    if eof :
        raise EOFError("Cannot move forward.")

    last_segms_len[:] = np.linalg.norm(segm[3:]-segm[:3])

    k = 0
    eof = False
    while not eof and k <80:
        segments += [segm]
        lines += [line]
        planes += [face1]

        # ---- Auto spacing ----
        # Evaluate the cuvature between the curent plane and the newone to set the suited spacing
        # Rolling the values
        last_segms_len[0] = np.linalg.norm(segm[3:]-segm[:3])
        face_tmp = face1
        for i in range(2):
            # half step forward
            face_tmp, line, segm, eof = plane_slice(face_tmp, face2, spacing_auto/2, min_tip_distance, height)

            if eof:
                segments += [segm]
                lines += [line]
                planes += [face_tmp]
                return planes, lines, np.array(segments)

            last_segms_len[i+1] = np.linalg.norm(segm[3:]-segm[:3])
            last_spacings[i] = spacing_auto/2

        dd_len = (last_segms_len[2]-last_segms_len[1])/last_spacings[1]
        dd_len -= (last_segms_len[1]-last_segms_len[0])/last_spacings[0]
        dd_len /= np.mean(last_spacings)
        spacing_auto = spacing/(1+np.abs(dd_len)*auto_spacing_coeff*spacing)
        # ---------------------

        print(f"{spacing_auto=}")
        face1, line, segm, eof = plane_slice(face1, face2, spacing_auto, min_tip_distance, height)
        k += 1

    return planes, lines, np.array(segments)


def test():
    wing_name = "wing_example"
    profil_file_path = "hq209.dat"

    doc = FreeCAD.ActiveDocument
    wing_objects = doc.findObjects(Label=wing_name+"*")
    print(wing_objects)

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
    sel = Selection.getSelectionEx()
    if len(sel) != 1:
        print("Please select two faces,the first face must coplanar withe the the wing first section.")

    if len(sel[0].SubObjects) != 2:
        print("Please select two faces,the first face must coplanar withe the the wing first section.")
        return 1

    face1 = sel[0].SubObjects[0]
    face2 = sel[0].SubObjects[1]

    _, _, endpts = faces_to_chordlines(face1, face2, spacing=30.0, auto_spacing_coeff=1.5)

    wing = Wing(doc, wing_name)
    wing.load_foilprofile(profil_file_path)

    names = [profil_file_path for i in range(endpts.shape[0])]

    wing.add_sections(names, endpts[:,:3], endpts[:,3:] , orientation=-1)
    sections = wing.make_part_sections()
    wing_obj = wing.build_wing_solid(sections)
    wing_obj.ViewObject.DisplayMode = "Shaded"

    doc.recompute()
    return 0

if __name__ == "__main__":
    test()
