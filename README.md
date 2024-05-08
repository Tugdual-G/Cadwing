# Cadwing
_**Create wings, fan, propeller or wind-turbine blades in FreeCAD with Python**_
This python script use two faces (from a surface or a solid) to generate a wing. 
The use of multiples airfoil is possible on the same wing.

The script will generate sections, and then apply a loft across them.
The curvature is computed to addapt the step between sections.

## Usage
Two faces must be selected. 
The first one serve as the wing root for the algorithm,
the chord of the subsequent airfoil sections will be parallel to this face.
The second face must represent the cordline. 

![GIF example](wingexample.gif)

