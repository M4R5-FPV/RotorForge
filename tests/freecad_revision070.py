import os
import sys,json,traceback,os
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,require_valid
from freecad.rotorforge import geometry as g,document as d,hardware_refs as hw
from freecad.rotorforge.nut_seats import seats
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True);checks=[];fail=[]
for design in ('2 plates','3 plates'):
 for mode in ('Recessed hex nut','M3 press nut'):
  try:
   p=Parameters(PlateDesign=design,ArmNutMount=mode);require_valid(p);shapes=g.build_shapes(p)
   for role in {s['role'] for s in seats(p)}:
    shape=shapes[role];flat=g.flat_plate_shape(shape,role,p);assert shape.isValid() and len(shape.Solids)==1
    if mode=='Recessed hex nut':assert flat.Volume>shape.Volume
   doc=App.newDocument();f=d.create_frame(p,doc);specs=hw.refresh(f);assert all(o.Shape.isValid() for o in hw.objects(f));App.closeDocument(doc.Name)
   checks.append(design+' / '+mode)
  except Exception:fail.append(dict(case=design+' / '+mode,error=traceback.format_exc()));traceback.print_exc()
(out/'native070.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print('DONE',len(checks),len(fail),flush=True)
