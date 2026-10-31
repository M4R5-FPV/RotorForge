# RotorForge

RotorForge is a FreeCAD workbench for designing two- and three-plate FPV quadcopter frames, inspecting individual parts and exporting manufacturing profiles.

Open **RotorForge_Help.pdf** for the current controls, illustrated workflows, materials, incremental updates and CNC export. Open **RotorForge_Installation.pdf** for Windows, macOS and Linux installation.

The editor covers motor layouts, arm roots and joints, plate outlines, stack and standoff mounting, camera cages and isolation, VTX mounting holes, LiPo pads, motor protectors, electronics side guards, cutouts, mass/CG estimates and cutting layouts. TPU / Appearance selects a shared colour for the printed and soft parts.

Create or Update builds affected components and reuses unchanged geometry. Save the FCStd after updating to retain verified cache data across reopening. Design and clearance checks remain active.

Version 0.89.1 corrects Between plates: side guards move inside the plate outlines and seat against the carrier and top plate faces for clamping. Side guard plate clearance controls the inward setback. Top-plate strap passages stay clear underneath; the joined wire opening and VTX opening remain available. The Help covers all 339 visible controls.

Version 0.88.0 speeds up saved-settings refresh and repeated frame creation. Successful builds are cached across FreeCAD sessions (up to eight designs and 128 MiB); matching native components are verified and reused while assembly checks remain active. Missing or damaged cache data falls back to normal generation. Parameter reads, validation, mass calculations and native display preparation avoid repeated work. The loading and caching improvements are retained in later releases.

Version 0.87.2 keeps top-plate strap outline cutouts clear beside the side guards. The guard bridges each opening along the outside edge of the plate. This happens automatically for one or two straps; the separate side-guard strap-opening controls remain available. Update saved frames and re-export the guard STEP/STL files after installing.

Version 0.87.1 fixes two-plate arm clamping. Below-bottom arms use one lower clamp and mount the FC stack on the bottom plate. Above-bottom arms use one upper clamp carrying the stack. The optional keystone adds no extra clamp. Both clamp ends continue to follow the arm roots.

When upgrading, close FreeCAD, replace the complete RotorForge folder, restart and use Update frame on existing projects or bundled older FCStd examples. Re-export cutting files to replace the previous clamp arrangement. Upper and lower clamp thicknesses remain saved separately.

The Help explains geometric checks, hardware fitting and the scope of mass estimates.

Copyright (c) 2026 Michael Struggl. Released under the MIT License; see LICENSE.

Hardware references show black round button-head screws, nuts and press nuts. Hardware / Nut retention adds hex nut pockets or M3 press-nut mounting bores to the receiving plates. Optional FC stack press nuts raise the stack and retain conventional upper nuts. VTX references use screws only.

Independent rear edge shaping is on each active plate page. Camera tab offsets on FPV / Side plates move the matching plate sockets and cutter reliefs with each tab. See the Help for profile catalogues and fit limits.

Frame / Top plate includes general front-edge profiles and six camera recesses with adjustable width, depth and shoulder setback. These settings define the top-front camera opening.

Finishing / Airflow and outlines includes numbered patterns, text and part filters, click-to-select with overlap cycling, highlighting and a selected-pattern zoom. Apply or discard edits before switching patterns.

TPU / Front bumper creates a separate bottom-plate shoe with eighteen nose styles, adjustable fit and retaining lip, automatic mounting-hole access and printable exports.

Front motor-wire pockets follow the local guard lower edge and curve around retained bearing sleeves when placed nearer the foremost standoffs.

Finishing / Detailed references optionally displays generic motors, three-blade propellers, a two-PCB FC/ESC stack with silicone grommets, a shaped FPV camera, VTX and LiPo in the 3D document. Each is enabled separately; the simple references remain the default. See the Help for sizing, bumper feature controls and presentation-model scope.
