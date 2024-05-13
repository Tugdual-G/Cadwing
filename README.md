# Cadwing
_**Create wings, fan, propeller or wind-turbine blades in FreeCAD with Python**_
This python script use two faces (from two surfaces or a solid) to generate a wing. 
This script makes building oddly curved and twisted wings easy.

The algorithm will generate sections, and then apply a loft across them.
The space between sections can be automatically adjusted from the curvature of the wing's shape.
Otherwise, it is possible to provide the desired spacing along different part of the wing.

The use of multiples airfoil is possible on the same wing.

![GIF example](wingexample.gif)

## Usage
The main script is cadwing.py.

Two faces must be selected in FreeCAD, or their names must be provided in the script. 
The first one serve as the wing root plane for the algorithm,
the chordline of the subsequent foil sections will be parallel to this face.
The second face must be the chordline surface, which gives the overall shape of the wing.

**Note** : The foil sections are perpendicular to the chordline surface.

The chordline surface can easily be drawn with the sketch workbench,
and then, using extrusion and boolean operations, it is easy to obtain a surface or a solid's face with the right shape.

The leading edge and trailing edges can be swapped in the python script.
The sections can also be flipped upside down.


If needed, the spacing between sections can be provided with an array of the following structure:

[[0, spacing value], ... ,[start of the new section, spacing value]]
 
example :

 [[0  , 30], # first section from 0 to 250 mm from the root's plane with 30 mm spacing\
  [250, 10], # second section from 250 to 340 mm from the root's plane with 10 mm spacing\
  [340, 20]] # third section from 340 mm until the tip of the wing with 20 mm spacing




