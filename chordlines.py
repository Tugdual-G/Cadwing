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


def face_sections(plane1_param, face2, space, min_tip_distance, height):
    """ Generate a new plane (plane2) *space* away from the plane 1
    and locally perpendicular to face2.
    Then computes the intersection line between plane2 and
    face2 in order to get the chordline.
    """

    length = height

    EndOfFace = False

    center = plane1_param[0]
    plane1_normal = plane1_param[1]

    # Move the center forward for the next plane section
    center = center - space*plane1_normal

    # find the normal of the shape's face at the new point
    uv = face2.Surface.parameter(Vector(*center))  # get the parameter u,v
    face2_normal = face2.normalAt(uv[0], uv[1])
    face2_normal = np.array([face2_normal.x, face2_normal.y, face2_normal.z])

    # Move the center of the next plane on the surface
    center = face2.Surface.value(uv[0],uv[1])
    center = np.array([center.x,center.y,center.z])

    # making the next section plane perpendicular to face2
    new_normal = plane1_normal-face2_normal*np.dot(face2_normal, plane1_normal)
    new_normal /= np.linalg.norm(new_normal)

    xaxis = np.cross(face2_normal, new_normal)
    xaxis /= np.linalg.norm(xaxis)
    zaxis = face2_normal
    zaxis = np.cross(xaxis,new_normal)
    zaxis /= np.linalg.norm(zaxis)

    if not face2.isInside(Vector(*center),0.00001,True):
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

    center = (segm_start+segm_end)/2
    return np.vstack((center, new_normal)), np.hstack((segm_start, segm_end)), EndOfFace


def faces_to_chordlines_auto(face1, face2, spacing, auto_spacing_coeff = 1.0, min_tip_distance=0.5):
    """ return a set of chordlines along the wing span. """

    height = face2.BoundBox.DiagonalLength

    last_segms_len = np.zeros(3)
    spacing_auto = spacing
    last_spacings = np.full(2,spacing_auto)
    segments = []
    planes = []

    # Get the center of intersection between the two surfaces
    segm = face2.section(face1)
    center = segm.CenterOfGravity

    segm_vert = segm.Vertexes
    if len(segm.Vertexes) !=2 :
        raise EOFError("The section segment should have 2 verticies.")

    segm_start = np.array([segm_vert[0].X,segm_vert[0].Y,segm_vert[0].Z])
    segm_end = np.array([segm_vert[1].X,segm_vert[1].Y,segm_vert[1].Z])
    segm = np.hstack((segm_start, segm_end))

    uv = face1.Surface.parameter(center)  # get the parameter u,v
    face1_normal = face1.normalAt(uv[0], uv[1])
    face1_normal = np.array([face1_normal.x, face1_normal.y, face1_normal.z])

    plane_param = np.vstack((center,face1_normal))

    last_segms_len[:] = np.linalg.norm(segm[3:]-segm[:3])

    k = 0
    eof = False
    while not eof and k <150:
        segments += [segm]
        planes += [plane_param]

        # ---- Auto spacing ----
        # Evaluate the cuvature between the curent plane and the newone to set the suited spacing
        # Rolling the values
        last_segms_len[0] = np.linalg.norm(segm[3:]-segm[:3])
        plane_tmp = plane_param
        for i in range(2):
            # half step forward
            plane_tmp, segm, eof = face_sections(plane_tmp, face2, spacing_auto/2, min_tip_distance, height)

            if eof:
                segments += [segm]
                planes += [plane_tmp]
                return planes, np.array(segments)

            last_segms_len[i+1] = np.linalg.norm(segm[3:]-segm[:3])
            last_spacings[i] = spacing_auto/2

        dd_len = (last_segms_len[2]-last_segms_len[1])/last_spacings[1]
        dd_len -= (last_segms_len[1]-last_segms_len[0])/last_spacings[0]
        dd_len /= np.mean(last_spacings)

        spacing_auto = spacing/(1+np.abs(dd_len)*auto_spacing_coeff*spacing)
        # ---------------------

        print(f"{spacing_auto=}")
        plane_param, segm, eof = face_sections(plane_param, face2, spacing_auto, min_tip_distance, height)
        k += 1

    return planes, np.array(segments)

def faces_to_chordlines(face1, face2, spacing_sections, min_tip_distance):
    """ return a set of chordlines along the wing span, using the provided set of spacings."""

    height = face2.BoundBox.DiagonalLength

    spacing_sections[:,0] = np.abs(spacing_sections[:,0])
    spacing_sections = np.vstack((spacing_sections,[height,5]))

    segments = []
    planes = []

    # Get the center of intersection between the two surfaces
    segm = face2.section(face1)
    center = segm.CenterOfGravity

    segm_vert = segm.Vertexes
    if len(segm.Vertexes) !=2 :
        raise EOFError("The section segment should have 2 verticies.")

    segm_start = np.array([segm_vert[0].X,segm_vert[0].Y,segm_vert[0].Z])
    segm_end = np.array([segm_vert[1].X,segm_vert[1].Y,segm_vert[1].Z])
    segm = np.hstack((segm_start, segm_end))

    uv = face1.Surface.parameter(center)  # get the parameter u,v
    face1_normal = face1.normalAt(uv[0], uv[1])
    face1_normal = np.array([face1_normal.x, face1_normal.y, face1_normal.z])

    plane_param = np.vstack((center,face1_normal))

    spacing = spacing_sections[0,1]
    sps_idx = 1 # Indicates the next section to come
    k = 0
    eof = False
    dist = 0.0
    while not eof and k <150:
        if dist >= (spacing_sections[sps_idx,0]-abs(np.dot(plane_param[1], face1_normal))*spacing - 0.0001):
            print(f"{dist =} , spacing = {spacing_sections[sps_idx,1]}")
            # Trying to reach the begining of the next section, not very accurate for highly curved wings.
            spacing = (spacing_sections[sps_idx,0]-dist)*abs(np.dot(plane_param[1], face1_normal))
            sps_idx += 1

        segments += [segm]
        planes += [plane_param]
        plane_param, segm, eof = face_sections(plane_param, face2, spacing, min_tip_distance, height)
        spacing = spacing_sections[sps_idx-1,1]
        dist += abs(np.dot((plane_param[0]-center),face1_normal))
        center = plane_param[0]
        k += 1

    return planes, np.array(segments)

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

    plane_param = sel[0].SubObjects[0]
    face2 = sel[0].SubObjects[1]

    _, endpts = faces_to_chordlines_auto(plane_param, face2, spacing=30.0, auto_spacing_coeff=1.5)

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
