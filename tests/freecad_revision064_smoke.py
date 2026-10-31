"""Native symmetry, rounded end support and independent vent section regression."""
import os,sys,json,traceback
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters,save_parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.protection_layout import guard_layout,guard_vents,guard_wire_openings,guard_vent_sections,grip_bridge
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];failures=[];figures={}
p=Parameters(FlexSideGuards=True,FlexGuardWireEnabled=True)
cases=[(design+'/'+style,replace(p,PlateDesign=design,FlexGuardStyle=style)) for design in ('2 plates','3 plates') for style in ('Solid','Vented')]
cases += [(design+'/wire width 12',replace(p,PlateDesign=design,FlexGuardStyle='Solid',FlexGuardWireWidth=12.)) for design in ('2 plates','3 plates')]
cases += [('VTX only',replace(p,FlexGuardFCVents=False,FlexGuardVentShape='Hexagons',FlexGuardSlotHeight=4.,FlexGuardVentWidth=8.)),('FC only',replace(p,FlexGuardVTXVents=False,FlexGuardFCVentShape='Diamonds')),('Independent sections',replace(p,FlexGuardVentShape='Hexagons',FlexGuardVentWidth=8.,FlexGuardSlotHeight=4.,FlexGuardFCVentShape='Rounded slots',FlexGuardFCVentWidth=9.,FlexGuardFCSlotHeight=2.5,FlexGuardVentBoundaryOffset=-2.,FlexGuardVTXVentZOffset=-1.,FlexGuardFCVentZOffset=1.)),('Six posts/front extension/USB',replace(p,FlexGuardExtendFront=True,FlexGuardUSBEnabled=True,FlexGuardUSBSide='Both',StandoffCount='6 (3 pairs)',StandoffPair3Y=-94.,StandoffPair3Width=28.,MidReachMode='Custom',MidRearReach=102.,TopReachMode='Custom',TopRearReach=102.)),('Round ends/insets',replace(p,FlexGuardStyle='Solid',FlexGuardFrontInset=3.,FlexGuardRearInset=3.)),('Round ends/22 mm posts',replace(p,FlexGuardStyle='Solid',StandoffHeight=22.)),('Eight posts/extra forward row',replace(p,FlexGuardExtendFront=True,StandoffCount='8 (4 pairs)',StandoffPair3Y=-94.,StandoffPair3Width=28.,StandoffPair4Y=60.,StandoffPair4Width=34.,MidReachMode='Custom',MidRearReach=102.,TopReachMode='Custom',TopRearReach=102.))]
def mesh(sh,role):
 v,f=sh.tessellate(.12);return dict(role=role,vertices=[list(a) for a in v],faces=f)
def edge_at(stock,y,sign):
 cap=max((f for f in stock.Faces if f.BoundBox.ZLength<1e-5),key=lambda f:f.Area);face=Part.Face(cap.OuterWire);z=face.BoundBox.ZMin
 cross=face.common(Part.makeLine(App.Vector(-1000,y,z),App.Vector(1000,y,z)));xs=[v.Point.x for v in cross.Vertexes if sign*v.Point.x>=-1e-6]
 return (max(xs) if sign>0 else min(xs)) if xs else None
for name,q in cases:
 try:
  s=build_shapes(q);left=s['ElectronicsGuardLeft'];right=s['ElectronicsGuardRight']
  assert left.isValid() and right.isValid() and len(left.Solids)==len(right.Solids)==1
  assert left.BoundBox.XMax<0 and right.BoundBox.XMin>0,'Guard crosses frame centre'
  assert abs(left.BoundBox.XLength-right.BoundBox.XLength)<1e-4,'Guard widths differ'
  assert abs(left.Volume-right.Volume)<.05,('Different volumes',left.Volume,right.Volume)
  matrix=App.Matrix();matrix.A11=-1.;mirrored=left.transformGeometry(matrix)
  assert mirrored.cut(right).Volume+right.cut(mirrored).Volume<.1,'Guards are not mirrors'
  for g in guard_layout(q):
   sh=s[g['role']];sign=g['sign']
   for index in (0,len(g['stands'])-1):
    st=g['stands'][index];sx,sy=st['point'];low,high=g['bands'][index]
    wall_y=max(g['rear']+q.FlexGuardRearInset,min(g['front']-q.FlexGuardFrontInset,sy));xt=edge_at(s['TopPlate'],wall_y,sign);xb=edge_at(s[g['lower_role']],wall_y,sign);xb=xt if xb is None else xb
    a,b,r=grip_bridge(q,g,st,(wall_y,xb+sign*q.FlexGuardClearance,xt+sign*q.FlexGuardClearance,low))
    probe=App.Vector(b[0]+sign*r*.8,sy+(1 if index==0 else -1)*r*.8,(low+high)/2)
    assert not sh.isInside(probe,1e-5,True),'Square outer end corner remains'
    bore=(q.StandoffDiameter+q.FlexGuardFit)/2
    for z in (low+.1,(low+high)/2,high-.1):
     assert sh.isInside(App.Vector(sx-sign*(bore+q.FlexGuardWall*.5),sy,z),1e-5,True),'Circular grip lost'
     assert not sh.isInside(App.Vector(sx,sy,z),1e-5,True),'Standoff bore obstructed'
   for v in guard_vents(q,g):
    probe=Part.makeBox(1000,v['width']*.1,v['height']*.1,App.Vector(-500,v['y']-v['width']*.05,v['z']-v['height']*.05));assert sh.common(probe).Volume<1e-5,'Vent blocked'
   for v in guard_wire_openings(q,g):
    probe=Part.makeBox(1000,v['width']*.3,v['height']*.5,App.Vector(-500,v['y']-v['width']*.15,v['bottom']-.1));assert sh.common(probe).Volume<1e-5,'Wire exit blocked'
  if name in ('VTX only','Independent sections'):
   figures[name]=dict(title=name,parts=[mesh(right,'ElectronicsGuardRight')],boundary=guard_vent_sections(q,guard_layout(q)[1])[0]['front'])
   save_parameters(Path(__file__).resolve().parents[1]/'examples'/('Example_VTXOnlyGuardVents.json' if name=='VTX only' else 'Example_IndependentGuardVents.json'),q)
  if name=='3 plates/Solid':
   parts=[]
   for role in ('BottomPlate','MidPlate','TopPlate','ElectronicsGuardLeft','ElectronicsGuardRight'):
    sh=s[role].copy()
    if role=='TopPlate':sh.translate(App.Vector(0,0,12))
    parts.append(mesh(sh,role))
   (out/'guards.json').write_text(json.dumps([dict(title='Rounded grips / matching left and right walls',parts=parts)]))
   for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):s[role].exportStep(str(out/(role+'.step')));s[role].exportStl(str(out/(role+'.stl')))
   d=App.newDocument('RoundGuards');obj=d.addObject('PartDesign::Feature','Guard');obj.Shape=right;d.recompute();d.saveAs(str(out/'RoundGuards.FCStd'));App.closeDocument(d.Name);d=App.openDocument(str(out/'RoundGuards.FCStd'));assert d.Guard.Shape.isValid();App.closeDocument(d.Name);checks.append('Guard native save/reopen and STEP/STL exports')
   # Two horizontal sections through the actual foremost post support.
   g=guard_layout(q)[1];st=g['stands'][0];sx,sy=st['point'];lo,hi=g['bands'][0];scenes=[]
   for z,title in ((hi-1,'Upper grip / electronics on the left'),(lo+1,'Lower grip / local carbon clearance')):
    region=Part.makeBox(20,14,.1,App.Vector(sx-7,sy-7,z));section=right.common(region)
    cap=max((f for f in section.Faces if f.BoundBox.ZLength<1e-5),key=lambda f:f.Area);wires=[cap.OuterWire]+[w for w in cap.Wires if not w.isSame(cap.OuterWire)]
    scenes.append(dict(title=title,parts=[dict(role='ElectronicsGuardRight')],loops=[[[v.x,v.y] for v in w.discretize(Deflection=.001)] for w in wires]))
   (out/'grip_sections.json').write_text(json.dumps(scenes));(out/'guard_plan.json').write_text(json.dumps([mesh(left,'ElectronicsGuardLeft'),mesh(right,'ElectronicsGuardRight')]))
  checks.append(name);print('PASS',name,flush=True)
 except Exception:failures.append(dict(name=name,error=traceback.format_exc()));traceback.print_exc()
(out/'vent_sections.json').write_text(json.dumps(list(figures.values())))
(out/'revision064.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
