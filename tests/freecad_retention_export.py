import os
import sys,json,traceback,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge import geometry as g,document as d,hardware_refs as hw
from freecad.rotorforge.parameters import Parameters,require_valid
from freecad.rotorforge.nut_seats import seats
from freecad.rotorforge.exporters import export_package
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];fail=[]
for label,p in [('above',Parameters(PlateDesign='2 plates',TwoPlateArmPosition='Above bottom plate',StackMountHeight=6.,StandoffHeight=40.,ArmNutMount='Recessed hex nut')),('clamp',Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,ArmNutMount='M3 press nut',PressNutFlangeRecess=.2)),('stack',Parameters(StackPressNuts=True,PressNutFlangeRecess=.2))]:
 try:
  require_valid(p);doc=App.newDocument();f=d.create_frame(p,doc);hw.refresh(f)
  for s in seats(p):assert d.component_objects(f)[s['role']].Shape.isValid()
  if label=='stack':
   folder=export_package(f,out/'Export');ops=list(csv.DictReader((folder/'MachiningOps.csv').open()));assert len(ops)==4
   assert all(row['face']=='Upper' and row['operation']=='Press-nut flange counterbore' for row in ops)
  if label=='above':
   folder=export_package(f,out/'Export');ops=list(csv.DictReader((folder/'MachiningOps.csv').open()));assert all(row['operation']=='Hex nut pocket' for row in ops)
  App.closeDocument(doc.Name);checks.append(label)
 except Exception:fail.append(dict(case=label,error=traceback.format_exc()));traceback.print_exc()
(out/'extra070.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print('DONE',checks,len(fail),flush=True)
