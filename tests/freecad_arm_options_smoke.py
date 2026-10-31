"""FreeCADCmd: arm keys/braces, above/below sandwiches and FPV top coverage."""
from dataclasses import replace
from itertools import combinations
import csv
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from freecad.rotorforge.parameters import Parameters, TWO_PLATE_ARM_POSITIONS, STANDOFF_COUNTS, arm_layouts, plate_levels, standoff_layouts, stack_holes, arm_brace_layouts, arm_clamp_grip, top_bounds
from tests.frame_cases import FRAME_CASES, FPV_CASES
from freecad.rotorforge.geometry import (build_shapes,carbon_roles,physical_roles,ARM_LOCK_ROLES,cylinder,rounded_plate)
from freecad.rotorforge.fpv import camera_slots
from freecad.rotorforge.document import create_frame,update_frame,component_objects,read_parameters
from freecad.rotorforge.exporters import export_package,profile_entities

output=Path(os.environ.get('ROTORFORGE_TEST_OUTPUT',tempfile.mkdtemp(prefix='rotorforge-arm-options-')))
output.mkdir(parents=True,exist_ok=True)
report={'status':'running','freecad_version':'.'.join(App.Version()[:3]),'checks':[],'export_folders':[]}

def check(ok,message):
    if not ok:raise AssertionError(message)
    report['checks'].append(message)

def valid_assembly(p,tag):
    s=build_shapes(p)
    for role in carbon_roles(p):
        check(s[role].isValid() and len(s[role].Solids)==1,tag+': connected '+role)
    for a,b in combinations(physical_roles(p),2):
        if s[a].BoundBox.intersect(s[b].BoundBox):
            check(s[a].common(s[b]).Volume<1e-6,tag+': no overlap '+a+'/'+b)
    return s

try:
    for name,p in FRAME_CASES.items():
        for clearance in (0,.1):
            q=replace(p,FPVEnabled=True,KeystoneEnabled=True,KeystoneClearance=clearance)
            s=valid_assembly(q,name+'/key/'+str(clearance));key=s['ArmKeystone']
            check(abs(key.BoundBox.ZMin-q.BottomThickness)<1e-7 and abs(key.BoundBox.ZLength-q.ArmThickness)<1e-7,
                  name+': key stock fills arm layer')
            check(key.distToShape(s['BottomPlate'])[0]<1e-7 and key.distToShape(s['MidPlate'])[0]<1e-7,
                  name+': key captured between bottom and mid')
            for arm in arm_layouts(q):
                check(abs(key.distToShape(s['Arm'+arm['name']])[0]-clearance)<1e-5,name+': fitted key seat '+arm['name'])
            for pt in stack_holes(q):
                probe=cylinder(*pt,q.StackAccessDiameter/2-.05,-.1,plate_levels(q)['deck_z']+.2)
                check(probe.common(key).Volume<1e-7,name+': clear 6 mm key access relief')
            check(any(e[0] in ('CIRCLE','ARC') and abs(e[3]-3)<1e-7 for e in profile_entities(key)),name+': access curves in flat profile')
        for position in TWO_PLATE_ARM_POSITIONS:
            for count in STANDOFF_COUNTS:
                for shared in (False,True):
                    q=replace(p,FPVEnabled=True,PlateDesign='2 plates',TopWidth=50,TwoPlateArmPosition=position,
                              ArmBracesEnabled=True,StandoffCount=count,StandoffHeight=30,
                              StandoffFrontMount='Arm outer hole' if shared else 'Custom position',
                              StandoffRearMount='Arm outer hole' if shared else 'Custom position')
                    if shared and count!=STANDOFF_COUNTS[0]:q=replace(q,StandoffPair3Mount='Rear arm inner hole')
                    if shared and count==STANDOFF_COUNTS[2]:q=replace(q,StandoffPair4Mount='Front arm inner hole')
                    tag=name+'/'+position+'/'+count+'/'+str(shared);s=valid_assembly(q,tag)
                    check(s['MidPlate'].isNull() and s['ArmKeystone'].isNull(),tag+': inactive three-plate parts omitted')
                    for b in arm_brace_layouts(q):
                        shape=s[b['role']]
                        check(abs(shape.BoundBox.ZMin-b['z'])<1e-7 and abs(shape.BoundBox.ZLength-q.ArmBraceThickness)<1e-7,
                              tag+': brace stock and mounting level')
                        if position.startswith('Above'):
                            for arm in arm_layouts(q):
                                check(shape.distToShape(s['Arm'+arm['name']])[0]<1e-7,tag+': clamp seats on '+arm['name'])
                        else:
                            check(shape.distToShape(s['BottomPlate'])[0]<1e-7,tag+': clamp seated above bottom')
                        extra=sum(st['mount']=='Arm clamp plate' and not st['shared_arm'] for st in standoff_layouts(q))
                        check(sum(e[0]=='CIRCLE' for e in profile_entities(shape))==12+extra,tag+': eight root plus four FC bores and free support holes')
                        check(shape.isInside(App.Vector(0,0,b['z']+b['thickness']/2),1e-7,True),tag+': continuous central FC platform')
                        for pt in b['bolts']:
                            z=min(b['z'],-q.ArmThickness,0)-.1
                            top=plate_levels(q)['top_z']+q.TopThickness+.1
                            probe=cylinder(*pt,q.RootHoleDiameter/2-.05,z,top-z)
                            for role in physical_roles(q):
                                # Top has bores only at selected shared supports.
                                if role!='TopPlate' or any(math.dist(pt,st['point'])<1e-6 for st in standoff_layouts(q)):
                                    check(probe.common(s[role]).Volume<1e-6,tag+': coaxial root fastener path '+role)
                    stands=standoff_layouts(q)
                    check(all(abs(st['base']+st['length']-plate_levels(q)['top_z'])<1e-7 for st in stands),tag+': level top')
                    check(next(st['length'] for st in stands if st['position']=='Rear')==q.StandoffHeight,tag+': rear height is actual hardware length')
    for rear,front in (('Custom position','Arm outer hole'),('Arm outer hole','Custom position')):
        p=replace(FPV_CASES['5-inch FPV Deadcat'],PlateDesign='2 plates',TwoPlateArmPosition='Above bottom plate',
                  ArmBracesEnabled=True,StandoffHeight=30,StandoffRearMount=rear,StandoffFrontMount=front)
        valid_assembly(p,'Mixed arm / bottom mounts')
        check(len({s['length'] for s in standoff_layouts(p)})==2,'Mixed mounting surfaces give two hardware lengths')
    for width in (14,19,28):
        p=replace(Parameters(),FPVEnabled=True,CameraWidth=width,CameraHeight=width,StandoffHeight=35,TopFrontShape='Camera U recess',TopFrontRecessWidth=14.,TopFrontDepth=28.,TopFrontSetback=0.)
        s=build_shapes(p);top=plate_levels(p)['top_z']
        point=App.Vector(0,p.CameraMountY,top+p.TopThickness/2)
        check(not s['TopPlate'].isInside(point,1e-7,True),'Open front camera notch, width '+str(width))
        for a,b,r in camera_slots(p):
            pt=((a[0]+b[0])/2,(a[1]+b[1])/2)
            check(not s['TopPlate'].isInside(App.Vector(*pt,top+1),1e-7,True),'Upper camera slot preserved')
        cover=Part.makeBox(p.VTXWidth,p.VTXLength,.1,App.Vector(-p.VTXWidth/2,p.VTXOffsetY-p.VTXLength/2,top+.5))
        check(cover.cut(s['TopPlate']).Volume<1e-6,'Top fully covers VTX rectangle')
    # The raised lens actually crosses the top plane and clears only because
    # of the U cutout. The camera body remains below the top.
    p=replace(Parameters(),FPVEnabled=True,PlateDesign='2 plates',StandoffHeight=32,TopFrontShape='Camera U recess',TopFrontRecessWidth=14.,TopFrontDepth=32.,TopFrontSetback=0.,
              CameraTilt=60,CameraTiltMax=60,CameraPivotMode='Custom height',CameraPivotHeight=17)
    s=build_shapes(p);top=plate_levels(p)['top_z'];rear,front=top_bounds(p)
    uncut=rounded_plate(p.TopWidth,front-rear,p.CornerRadius,top,p.TopThickness,(front+rear)/2)
    check(s['CameraEnvelope'].common(uncut).Volume>1,'Raised lens would intersect an uncut top')
    check(s['CameraEnvelope'].common(s['TopPlate']).Volume<1e-6,'Front cutout clears a physically raised lens')
    bad=replace(p,TopFrontRecessWidth=3)
    try:build_shapes(bad)
    except ValueError:check(True,'Cutout too narrow for raised lens rejected by actual collision check')
    else:raise AssertionError('Narrow notch accepted')
    doc=App.newDocument('RotorForgeArmOptions');settings=create_frame(doc=doc)
    packages=[replace(FPV_CASES['5-inch FPV Deadcat'],KeystoneEnabled=True)]
    for pos in TWO_PLATE_ARM_POSITIONS:
        packages.append(replace(FPV_CASES['5-inch FPV Deadcat'],PlateDesign='2 plates',TwoPlateArmPosition=pos,
                                ArmBracesEnabled=True,ArmBraceThickness=2.5,StandoffHeight=30))
    packages.append(replace(packages[-1],ArmBracesEnabled=False,StackMountHeight=5.2))
    for index,p in enumerate(packages):
        update_frame(settings,p);folder=export_package(settings,output);report['export_folders'].append(str(folder))
        rows=list(csv.DictReader((folder/'PartsList.csv').open()))
        shapes=build_shapes(p)
        check(abs(settings.CarbonMassGrams-sum(shapes[r].Volume for r in carbon_roles(p))*p.CarbonDensity/1000)<1e-7,
              'Optional arm stock included in carbon mass')
        step=Part.read(str(folder/'FrameAssembly.step'))
        check(step.isValid() and len(step.Solids)==len(carbon_roles(p))+4,'Assembly STEP includes active arm locking parts only')
        for role in ARM_LOCK_ROLES:
            check((folder/'CuttingProfiles'/(role+'.dxf')).exists()==(role in carbon_roles(p)),role+': conditional flat export')
        grip=next(float(r['Thickness_mm']) for r in rows if r['Part']=='Arm clamp bolts into standoffs')
        check(grip==arm_clamp_grip(p),'Clamp bolt BOM includes actual sandwich thickness')
        check(sum(int(r['Quantity']) for r in rows if r['Part'] in ('Arm root bolts','Arm clamp bolts into standoffs'))==8,
              'Combined clamp reuses the eight root fasteners')
        metadata=json.loads((folder/'ExportInfo.json').read_text())
        check(metadata['fpv']['top_camera_cutout']['depth']>0,'Cutout dimensions exported')
        check(metadata['arm_mounting']['clamp_grip_mm']==arm_clamp_grip(p),'Arm mounting metadata exported')
        path=output/f'ArmOptions_{index}.FCStd';doc.saveAs(str(path));name=settings.Name;App.closeDocument(doc.Name)
        doc=App.openDocument(str(path));settings=doc.getObject(name);doc.recompute()
        check(read_parameters(settings)==p,'New options persist in native document')
    doc.UndoMode=1;update_frame(settings,Parameters());doc.undo();doc.recompute()
    check(read_parameters(settings).TwoPlateArmPosition=='Above bottom plate','Undo restores arm placement')
    legacy=App.openDocument(str(Path(__file__).parent/'fixtures/Legacy_0.5.FCStd'))
    old=legacy.getObject('FrameParameters');update_frame(old,replace(read_parameters(old),KeystoneEnabled=True))
    check(not component_objects(old)['ArmKeystone'].Shape.isNull(),'Existing document gains optional keystone component')
    report['status']='passed'
except Exception:
    report['status']='failed';report['error']=traceback.format_exc()
finally:
    for d in list(App.listDocuments().values()):App.closeDocument(d.Name)
    (output/'test_report.json').write_text(json.dumps(report,indent=2))
