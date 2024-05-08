import FreeCAD
from FreeCAD import Vector
import numpy as np
import sys
sys.path.insert(0,'/home/tugdual/cad/')
from airfoil import wing_section, foil_profile, generate_normal
import Draft
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
        self.baseprofiles[foil_name] = foil_profile(filename)

    def add_sections(self, profile_names, lead_pos, trail_pos, orientation = 1, normals = None):

        if normals == None:
            normal_vects = orientation*generate_normal(lead_pos, trail_pos)
        else :
            normal_vects = orientation*normals

        for name, l_pos, t_pos, normal in zip(profile_names, lead_pos, trail_pos, normal_vects):
            sec = wing_section(self.baseprofiles[name])
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

    def draw_wire_sections(self, polygon_sections):
        for i,sec in enumerate(polygon_sections):
            part2d = Draft.make_wire(sec)
            part2d.Label = f"{self.name}_section{i}"

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
        return loft_obj


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

    if DOC is None:
        FreeCAD.newDocument(DOC_NAME)
        FreeCAD.setActiveDocument(DOC_NAME)
        DOC = FreeCAD.activeDocument()

    while len(DOC.Objects) > 0:
        FreeCAD.ActiveDocument.removeObject(FreeCAD.ActiveDocument.Objects[0].Name)



    wing = Wing(DOC, "wing_example")
    filename = "/home/tugdual/cad/hq209.dat"
    wing.load_foilprofile(filename)


    xyz_ls, xyz_ts = ellipse(15, 5, 25)
    xyz_ls[:,2] = (1/19*xyz_ls[:,1])**6
    xyz_ts[:,2] = (1/19*xyz_ts[:,1])**6
    normal = np.zeros_like(xyz_ls)
    normal[:,1] = -1
    normal[:,2] = -6/19*(1/19*xyz_ls[:,1])**5
    names = [filename for i in range(len(normal))]

    wing.add_sections(names, xyz_ls, xyz_ts, orientation=-1)
    sections = wing.make_part_sections()
    wing.build_wing_solid(sections)
    #wing.draw_wire_sections(sections)
    DOC.recompute()
