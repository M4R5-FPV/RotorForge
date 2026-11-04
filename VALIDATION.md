# v0.90.8 performance validation

- 513 unit tests passed, including cache ownership, invalidation and dependency provenance.
- Zoom/pan reuse the recorded vector drawing; dimensions, modes and resize invalidate it.
- Eight assembly cases compared old/new guards and VTX/ELRS mounts by bidirectional solid differences (32 solid comparisons).
- Save/reopen and reference export checks passed; unchanged guards and VTX are reused after an ELRS edit.
- All 374 Help control labels, defaults and enumeration choices match current editor/schema; updated pages visually reviewed.
- Timings and limitations: `docs/performance_validation.json`.

# RotorForge 0.89.3 validation

- All 479 portable regression tests passed. Two preview-fillet tests passed again after adding press-nut footprint protection to the general fillet code.
- 18 native checks passed using conda-forge FreeCAD reporting 26.3.0 and Python 3.11.
- Automatic mounting junctions on arm roots and plates have tangent blends; exact checks confirm no original material is removed and no sharp re-entrant mounting junction remains in the tested outlines.
- Press-nut cases cover configured minimum web greater than 1 mm, larger flanges, recessed flange pockets, FC-stack insert pads, and general edge fillets. Full bearing rings around the actual flange/counterbore were checked against the final solids.
- Existing checks cover two/three plates, upper/lower clamps, fitted roots, shared standoffs, valid connected carbon solids, native save/reopen, reversible extension growth and STEP/DXF/SVG exports.
- Help (102 pages, 339 controls) and Installation (2 pages) rebuilt and visually reviewed. The requested Windows FreeCAD v1-1 path remains unchanged.
- No physical fabrication or structural load test was performed.


## v0.89.4 category icons

Native FreeCAD UI checks passed for all seven main categories, unchanged subsection text tabs, all field search targets, default parameter preservation and the original workbench commands. Geometry code is byte-identical to v0.89.3. No modular trial editors are included. Tested on Linux FreeCAD 26.3.0 with Qt offscreen; Windows was not tested.


## v0.89.5 editor layout

479 portable tests passed. Native Linux FreeCAD 26.3.0 / Qt offscreen checks passed for vertical category navigation, wrapping TPU buttons, all field search targets, pointer-centred zoom/reset, preview painting, Airflow add/apply/discard/remove, default preservation, maximize support and bottom search placement. Airflow has no outer scroll at 950 x 650 in the tested environment. See docs/validation0895.json and tests/freecad_editor_navigation.py. Windows scaling was not tested. Geometry algorithms are unchanged.


## v0.89.6 saved reference hardware

Four portable preference tests passed, covering JSON roundtrip, legacy files, explicit off and validation before file overwrite. Seven native FreeCAD GUI integration checks passed for the actual editor Save/Load/Create path, screws and press nuts, hidden/per-owner visibility, save before build, exported settings, explicit no-hardware and legacy behavior. See docs/validation0896.json and tests/freecad_hardware_json.py. Tested on Linux FreeCAD 26.3.0 offscreen; Windows was not tested.
