import sys,os,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part,MeshPart
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,plate_levels
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.protection_layout import guard_layout,usb_window
from freecad.rotorforge.mesh_cleanup import weld_micro_seams
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[]
for design in ('2 plates','3 plates'):
 p=Parameters(PlateDesign=design,FPVEnabled=True,StandoffHeight=35.,FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardUSBEnabled=True,FlexGuardStyle='Solid')
 g.build_for_update(p)
 top=guard_layout(p)[0]['top']-guard_layout(p)[0]['deck_z']
 for z in (top-12,top-8,top-5,top-3,top-1):
  q=replace(p,FlexGuardUSBZ=z);parts=g.build_for_update(q)
  assert set(g.build_report(q)['rebuilt'])<={'ElectronicsGuardLeft','ElectronicsGuardRight','FrameCGMarker'}
  s=parts['ElectronicsGuardLeft'];assert s.isValid() and len(s.Solids)==1
  mesh=weld_micro_seams(MeshPart.meshFromShape(Shape=s,LinearDeflection=.08,AngularDeflection=.2,Relative=False));assert mesh.isSolid()
  mesh.write(str(out/(design[0]+'USB'+str(int(z))+'.stl')))
  # Each cutter actually removes the requested centre region at the outer wall.
  layout=guard_layout(q)[0];wy,wz,ww,wh=usb_window(q,layout)
  assert not s.isInside(App.Vector(layout['x']-layout['sign']*.5,wy,min(layout['top']-.5,layout['deck_z']+z)),1e-6,True)
  checks.append(['high USB, one solid and closed STL',design,z])
 for style in ('Slots','Outline cutouts'):
  q=replace(p,StrapCount='1 strap',StrapSingleY=-4.,StrapOpeningStyle=style)
  parts=g.build_for_update(q);s=parts['TopPlate'];assert s.isValid() and len(s.Solids)==1
  s.exportStep(str(out/(design[0]+style.replace(' ','')+'.step')));checks.append(['single strap',design,style])
q=replace(p,StrapCount='1 strap',StrapSingleY=-4.,StrapOpeningStyle='Outline cutouts',FlexGuardUSBZ=24.)
doc=App.newDocument();frame=d.create_frame(q,doc);doc.saveAs(str(out/'StrapsUSB086.FCStd'));App.closeDocument(doc.Name)
doc=App.openDocument(str(out/'StrapsUSB086.FCStd'));assert d.read_parameters(doc.getObject('FrameParameters'))==q;App.closeDocument(doc.Name)
checks.append('save/reopen');(out/'checks.json').write_text(json.dumps(checks,indent=2));print('PASS',len(checks),flush=True)
