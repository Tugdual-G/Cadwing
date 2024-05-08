#!/usr/bin/env python
from logging import raiseExceptions
import numpy as np
import warnings

class FoilProfile():
    def __init__(self, filename, skiprows=1):
        self.filename = filename
        self.xz = np.loadtxt(filename, skiprows=skiprows)

        # In case of the file not returning to the starting point
        if not np.array_equal(self.xz[-1,:], self.xz[0,:]) :
            print("Adding closing endpoint to the foil profile")
            self.xz = np.append(self.xz, [self.xz[0,:]],axis=0)

        self.find_edges()

    def find_edges(self):
        segments = self.xz[1:,:]-self.xz[:-1,:]
        self.segm_vector = segments/np.sqrt(segments[:,0]**2+segments[:,1]**2)[:,np.newaxis]
        segm_vector =self.segm_vector

        pre_scalarprod = np.zeros((self.xz.shape[0]-1,2))
        pre_scalarprod[1:,:] = segm_vector[1:,:]*(-segm_vector[:-1,:])
        pre_scalarprod[0,:] = segm_vector[0,:]*(-segm_vector[-1,:])
        self.scalarprod = np.sum(pre_scalarprod, axis=1)
        self.leading_edge_idx, self.trailing_edge_idx = np.argsort(self.scalarprod)[-2:]

class WingSection():
    def __init__(self, base_profile):
        self.base_prof = base_profile


        # Creating the 3d section from the 2d base profile
        self.xyz = np.zeros((self.base_prof.xz.shape[0],3))
        self.xyz[:,[0,2]] = self.base_prof.xz[:,:]

        self.lead_pos = self.xyz[self.base_prof.leading_edge_idx,:]
        self.trail_pos = self.xyz[self.base_prof.trailing_edge_idx,:]

        # The profile orientation
        chord_vect = self.trail_pos - self.lead_pos
        self.chord = np.sqrt(np.sum((chord_vect)**2))
        chord_vect = chord_vect/self.chord
        normal_vect = np.array([0.0, 1.0, 0.0])

        # local basis of unit vectors
        self.local_basis = np.column_stack((chord_vect,normal_vect, np.cross(chord_vect,normal_vect)))



    def transform(self, lead_pos, trail_pos, normal_vect):

        trail_pos, lead_pos = np.array(trail_pos), np.array(lead_pos)
        if trail_pos.size != 3 or lead_pos.size != 3 or lead_pos.size != 3 :
            raise ValueError("Wrong number of coordinates, please provide 3D space vectors")


        new_chord_vect = np.array(trail_pos) - np.array(lead_pos)
        new_chord = np.linalg.norm(new_chord_vect)
        if new_chord < 0.05 :
            warnings.warn("This section is really small (<0.05 mm), Freecad may not be able to build it", RuntimeWarning)

        new_chord_vect = new_chord_vect/new_chord

        new_normal_vect = np.array(normal_vect)
        new_normal_vect = new_normal_vect/np.linalg.norm(new_normal_vect)

        if 0.0001 < abs(np.dot(new_normal_vect, new_chord_vect)):
            raise ValueError("normal vector is not normal to the chord")

        new_thick_vect = np.cross(new_chord_vect,new_normal_vect)
        new_thick_vect = new_thick_vect/np.linalg.norm(new_thick_vect)

        new_local_basis = np.column_stack((new_chord_vect,new_normal_vect, new_thick_vect))



        # transform
        # P_o1 P_12 P_1o V_o = P_o2 P_o1_inv V_o
        # = P_o2 * P_o1.T/chord * V_o
        self.xyz = new_chord/self.chord*(new_local_basis @ (self.local_basis.T @ self.xyz.T)).T


        # Update attributes
        self.chord = new_chord
        self.local_basis[:] = new_local_basis

        # do not change the order
        self.lead_pos = self.xyz[self.base_prof.leading_edge_idx,:]
        self.trail_pos = self.xyz[self.base_prof.trailing_edge_idx,:]
        self.translate_lead(lead_pos)


    def scale(self, factor):
        l_pos = self.lead_pos.copy()
        self.xyz = self.xyz*factor
        self.translate_lead(l_pos)
        # Update
        self.trail_pos = self.xyz[self.base_prof.trailing_edge_idx,:]
        self.lead_pos = self.xyz[self.base_prof.leading_edge_idx,:]

    def translate_lead(self, new_lead_pos):
        self.xyz = self.xyz+(new_lead_pos - self.lead_pos)
        # Update
        self.lead_pos = self.xyz[self.base_prof.leading_edge_idx,:]
        self.trail_pos = self.xyz[self.base_prof.trailing_edge_idx,:]


def generate_normal(lead_pos, trail_pos):
    trail_pos, lead_pos = np.array(trail_pos), np.array(lead_pos)

    if trail_pos.size != lead_pos.size:
        raise ValueError("Arguments shapes don't match")

    if trail_pos.shape[1] != 3 or lead_pos.shape[1] != 3:
        raise ValueError("Wrong number of coordinates, please provide set of n 3D space coordinates : (n, 3)")

    if lead_pos.shape[0] < 2 :
        raise ValueError("Please provide more than one couple of coordinates")

    lead_pos, trail_pos = np.array(lead_pos), np.array(trail_pos)
    chord_vect = (trail_pos-lead_pos)/np.linalg.norm(trail_pos-lead_pos, axis=1,keepdims=True)
    center_pos = (lead_pos+trail_pos)/2
    norm_vect = np.zeros_like(lead_pos)

    if norm_vect.shape[0] == 2 :
        norm_vect[:,:] = (center_pos[1,:]-center_pos[0,:])[np.newaxis,:]
    else :
        norm_vect[1:-1,:] = center_pos[2:,:]-center_pos[:-2]
        norm_vect[0,:] = center_pos[1,:]-center_pos[0,:]
        norm_vect[-1,:] = center_pos[-1,:]-center_pos[-3,:]

    norm_vect = norm_vect - chord_vect*(np.sum(chord_vect*norm_vect,axis=1,keepdims=True))
    norm_vect /= np.linalg.norm(norm_vect,axis=1,keepdims=True)

    return norm_vect


def test_foilProfile():
    import matplotlib.pyplot as plt


    foil = FoilProfile( "hq209.dat")

    plt.quiver(foil.xz[:-1,0],foil.xz[:-1,1],foil.segm_vector[:,0], foil.segm_vector[:,1], angles='xy', width=0.001, scale=50)
    plt.scatter(foil.xz[:-1,0],foil.xz[:-1,1],c=foil.scalarprod, marker=".")
    plt.plot(foil.xz[foil.trailing_edge_idx,0],foil.xz[foil.trailing_edge_idx,1], 'x', linewidth=5)
    plt.plot(foil.xz[foil.leading_edge_idx,0],foil.xz[foil.leading_edge_idx,1], 'x', linewidth=5)
    plt.gca().set_aspect('equal')
    plt.show()

def test_wing_section():
    import matplotlib.pyplot as plt

    def ellipse(n, a=1.0, b=2):
        t = np.linspace(0.0, np.pi/2, n)
        x_l = a*np.cos(t)
        y_l = b*np.sin(t)
        x_t = -x_l
        y_t = y_l
        return np.column_stack((x_l,y_l,np.zeros_like(x_l))), np.column_stack((x_t,y_t,np.zeros_like(x_l)))

    foil = FoilProfile("hq209.dat")
    sec = WingSection(foil)


    ax = plt.figure().add_subplot(projection='3d')


    xyz_ls, xyz_ts = ellipse(12, 5, 25)

    xyz_ls[:,2] = (1/19*xyz_ls[:,1])**6
    xyz_ts[:,2] = (1/19*xyz_ts[:,1])**6
    ax.plot(*xyz_ls.T,'k')
    ax.plot(*xyz_ts.T,'k')
    normal = generate_normal(xyz_ls, xyz_ts)

    # Plotting the axis cross
    for xyz_l, xyz_t, norm in zip(xyz_ls, xyz_ts, normal):
        sec.transform(xyz_l, xyz_t, -norm)
        ax.plot(*sec.xyz.T,'k')
        c = np.array([sec.lead_pos,sec.lead_pos + 2*sec.local_basis[:,0]])
        n = np.array([sec.lead_pos,sec.lead_pos + 2*sec.local_basis[:,1]])
        t = np.array([sec.lead_pos,sec.lead_pos + 2*sec.local_basis[:,2]])
        ax.plot(*c.T,'b')
        ax.plot(*n.T,'g')
        ax.plot(*t.T,'r')

    ax.set_xlim3d(-10, 10)
    ax.set_ylim3d(0, 25)
    ax.set_zlim3d(-5, 20)
    plt.show()


if __name__=="__main__":
    # test_foilProfile()
    test_wing_section()
