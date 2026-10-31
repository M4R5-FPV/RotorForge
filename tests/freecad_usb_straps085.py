"""Native checks for USB placement and top-plate open strap cutouts."""
import sys,os,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,plate_levels,stack_reference_z
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.detailed_references import detailed_reference,stack_model,stack_dimensions
from freecad.rotorforge.reference_options import stack_usb_centre
from freecad.rotorforge.strap_openings import notch_polygons
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[]
for spacing in (20.,30.5):
 for side in ('Left','Right'):
  p=Parameters(DetailedStackReference=True,StackSpacing=spacing,StackUSBFace=side,StackUSBOffsetY=-2.,StackOffsetY=3.)
  shape,colours=detailed_reference(p,'StackEnvelope');assert shape.isValid() and len(shape.Faces)==len(colours)
  x,y,z=stack_usb_centre(p)
  # Socket opening is hollow, tongue visible, metal wall at its upper rim.
  point=lambda xx,yy,zz: App.Vector(xx,yy,zz)
  ix=x+(.1 if x<0 else -.1)
  assert not shape.isInside(point(ix,y,z+.8),1e-6,True)
  assert shape.isInside(point(ix,y,z+1.5),1e-6,True)
  _,cap,_,high,_=stack_dimensions(p.StackHeight)
  pcbtop=stack_reference_z(p)+high+min(1.4,p.StackHeight*.12)
  assert abs(z-1.6-pcbtop)<1e-6
  # All four opposing grommets still meet; cap and hardware heights unchanged.
  local,_=stack_model(spacing,p.StackHeight,p.StackHoleDiameter,side,-2.)
  for i in range(4):assert abs(local.Solids[i+1].BoundBox.ZMax-local.Solids[i+6].BoundBox.ZMin)<1e-6
  checks.append(['USB hollow shell, board seating and grommets',spacing,side])
for design in ('2 plates','3 plates'):
 p=Parameters(PlateDesign=design)
 base=g.build_for_update(p)
 for style in ('Outline cutouts','Slots'):
  q=replace(p,StrapOpeningStyle=style,DetailedStackReference=True)
  shapes=g.build_for_update(q);top=shapes['TopPlate'];assert top.isValid() and len(top.Solids)==1
  assert all(not r.startswith('Arm') for r in g.build_report(q)['rebuilt'])
  z=plate_levels(q)['top_z']+q.TopThickness/2
  for x in (-q.TopWidth/2+1,q.TopWidth/2-1):assert top.isInside(App.Vector(x,q.StrapOffsetY,z),1e-6,True)==(style!='Outline cutouts')
  top.exportStep(str(out/(design[0]+style.replace(' ','')+'.step')))
  assert Part.read(str(out/(design[0]+style.replace(' ','')+'.step'))).isValid()
  checks.append(['connected plate, unchanged arms and STEP',design,style])
# Shape variations and saved signed USB offset.
for kw in ({'TopCentreWidth':60.,'CentreSectionLength':60.},{'TopPlateShape':'Tapered front'},{'FPVEnabled':True}):
 p=Parameters(StrapOpeningStyle='Outline cutouts',DetailedStackReference=True,StackUSBOffsetY=-2.,**kw)
 s=g.build_for_update(p)['TopPlate'];assert s.isValid() and len(s.Solids)==1
 checks.append(['outline variant',kw])
doc=App.newDocument('USBStraps085');frame=d.create_frame(p,doc);doc.saveAs(str(out/'USBStraps085.FCStd'));App.closeDocument(doc.Name)
doc=App.openDocument(str(out/'USBStraps085.FCStd'));assert d.read_parameters(doc.getObject('FrameParameters'))==p;App.closeDocument(doc.Name)
checks.append('FCStd roundtrip')
(out/'native_checks.json').write_text(json.dumps(checks,indent=2));print('PASS',len(checks),flush=True)
