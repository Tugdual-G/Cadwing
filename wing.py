import FreeCAD
from FreeCAD import Vector
import numpy as np
from sys import path
path.append('/home/tugdual/cad/Cadwing')
from airfoil import WingSection, FoilProfile, generate_normal
import Draft
import Sketcher
import Part

class Wing(object):
    def __init__(self, doc,name="wing"):
        self.name = name
        self.baseprofiles = {}
        self.shape = None
        self.sections = []
        self.doc = doc


    def load_foilprofile(self, filename, foil_name=None):
        if foil_name == None:
            foil_name = filename
        self.baseprofiles[foil_name] = FoilProfile(filename)

    def add_sections(self, profile_names, lead_pos, trail_pos, orientation = 1, normals = None):

        if normals == None:
            normal_vects = orientation*generate_normal(lead_pos, trail_pos)
        else :
            normal_vects = orientation*normals

        for name, l_pos, t_pos, normal in zip(profile_names, lead_pos, trail_pos, normal_vects):
            sec = WingSection(self.baseprofiles[name])
            sec.transform(l_pos, t_pos, normal)
            self.sections += [sec]

    def make_part_sections(self):
        polygon_sections =  []
        for i, sec in enumerate(self.sections):
            points = []
            for pt in sec.xyz:
                points += [Vector(pt[0], pt[1], pt[2])]
            poly_section = Part.makePolygon(points)
            polygon_sections +=  [poly_section]
        return polygon_sections

    def make_spline_sections(self):
        spline_sections =  []
        for i, sec in enumerate(self.sections):
            points = []
            for pt in sec.xyz:
                points += [Vector(pt[0], pt[1], pt[2])]

            spline = Part.BSplineCurve()
            spline.interpolate(points)

            spline_sections +=  [spline.toShape()]

        return spline_sections

    def make_spline_sections_segmented(self, n_segments=0):
        spline_sections =  []
        for i, sec in enumerate(self.sections):
            # points = []
            # for pt in sec.xyz:
            #     points += [Vector(pt[0], pt[1], pt[2])]

            # spline = Part.BSplineCurve()
            # spline.interpolate(points)

            splines = []
            # lenght of the extrado segments

            l_idx = sec.base_prof.leading_edge_idx
            l_extrdo = l_idx/n_segments
            l_intrdo = (sec.xyz.shape[0]- l_idx)/n_segments

            for j in range(n_segments):
                points = []
                for pt in sec.xyz[int(j*l_extrdo) : int((j+1)*l_extrdo)+1]:
                    points += [Vector(pt[0], pt[1], pt[2])]

                spl = Part.BSplineCurve()
                spl.interpolate(points)
                splines += [spl]

                points = []
                for pt in sec.xyz[l_idx+int(j*l_intrdo): l_idx + int((j+1)*l_intrdo)+1-(j+1)//n_segments]:
                    points += [Vector(pt[0], pt[1], pt[2])]

                spl = Part.BSplineCurve()
                spl.interpolate(points)
                splines += [spl]

            spline_sections +=  [Part.makeCompound(splines)]
            # spline_sections +=  [spline.toShape()]

        return spline_sections

    def build_wing_solid(self, polygon_sections):
        section_objects = []
        for i, sec in enumerate(polygon_sections):
            obj = self.doc.addObject("Part::Feature",f"{self.name}_section{i}")
            obj.Shape = sec
            section_objects += [obj]

        loft_obj = self.doc.addObject("Part::Loft", f"{self.name}_loft")
        loft_obj.Sections = section_objects
        loft_obj.Solid=True
        loft_obj.Ruled=False
        return loft_obj, section_objects


if __name__ == "__main__":

    def ellipse(n, a=1.0, b=2):
        t = np.linspace(0.0, np.pi/2-0.05, n)
        x_l = a*np.cos(t)
        y_l = b*np.sin(t)
        x_t = -x_l
        y_t = y_l
        return np.column_stack((x_l,y_l,np.zeros_like(x_l))), np.column_stack((x_t,y_t,np.zeros_like(x_l)))

    DOC = FreeCAD.activeDocument()
    DOC_NAME = "wing"

    for obj in DOC.Objects:
        name = obj.Name
        DOC.removeObject(name)

    if DOC is None:
        FreeCAD.newDocument(DOC_NAME)
        FreeCAD.setActiveDocument(DOC_NAME)
        DOC = FreeCAD.activeDocument()

    while len(DOC.Objects) > 0:
        FreeCAD.ActiveDocument.removeObject(FreeCAD.ActiveDocument.Objects[0].Name)



    wing = Wing(DOC, "wing_example")
    filename = "/home/tugdual/cad/Cadwing/hq209.dat"
    wing.load_foilprofile(filename)


    xyz_ls, xyz_ts = ellipse(15, 5, 25)
    xyz_ls[:,2] = (1/19*xyz_ls[:,1])**6
    xyz_ts[:,2] = (1/19*xyz_ts[:,1])**6
    normal = np.zeros_like(xyz_ls)
    normal[:,1] = -1
    normal[:,2] = -6/19*(1/19*xyz_ls[:,1])**5
    names = [filename for i in range(len(normal))]

    wing.add_sections(names, xyz_ls, xyz_ts, orientation=-1)
    sections = wing.make_spline_sections_segmented(6)
    wing.build_wing_solid(sections)
    DOC.recompute()
