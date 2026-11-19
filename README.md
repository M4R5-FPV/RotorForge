# RotorForge

RotorForge is an open-source FreeCAD workbench for designing custom FPV quadcopter frames. Customize two- and three-plate frames, preview the assembly, and export 3D models and CNC cutting profiles.

For installation and usage, see the PDFs included in this folder:

* [Installation guide](RotorForge_Installation.pdf) — how to install and update RotorForge on Windows, macOS and Linux.
* [User guide](RotorForge_Help.pdf) — how the workbench works, its settings, and the workflow for designing and exporting a frame.



Copyright (c) 2026 Michael Struggl. Released under the [MIT License](LICENSE).


### TPU camera cage (experimental)
A single connected TPU cage follows the finished upper and lower carbon plate front contours. The lower centre is joined; the upper centre stays open. Adjust top rear reach, bottom rear reach, lower centre rear reach, and lower connection height independently under Camera cage → TPU attachment. Uses M3 clearance holes in the carbon and blind pockets for metal heat-set inserts in the TPU. Camera isolation is selected separately under TPU → Camera isolation. Older two-piece cage settings are migrated to the unified cage. Validate the exported STL and screw/insert clearances before printing.
