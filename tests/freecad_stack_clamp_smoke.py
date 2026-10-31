"""FreeCADCmd: combined FC clamp, removable-stack access and optional straps."""
from dataclasses import replace
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
from freecad.rotorforge.parameters import Parameters, TWO_PLATE_ARM_POSITIONS, stack_holes, strap_slots, plate_levels, stack_mounting_role, stack_reference_z
from tests.frame_cases import FRAME_CASES, FPV_CASES
from freecad.rotorforge.geometry import build_shapes,physical_roles,carbon_roles,cylinder
from freecad.rotorforge.document import create_frame,update_frame,read_parameters,component_objects
from freecad.rotorforge.exporters import export_package,profile_entities
from freecad.rotorforge.fpv import camera_mounts

output=Path(os.environ.get('ROTORFORGE_TEST_OUTPUT',tempfile.mkdtemp(prefix='rotorforge-stack-clamp-')))
output.mkdir(parents=True,exist_ok=True)
report={'status':'running','freecad_version':'.'.join(App.Version()[:3]),'checks':[],'export_folders':[]}

def check(ok,message):
    if not ok:raise AssertionError(message)
    report['checks'].append(message)

def circle_at(shape,point,radius):
    return any(e[0]=='CIRCLE' and math.dist((e[1],e[2]),point)<1e-7 and abs(e[3]-radius)<1e-7 for e in profile_entities(shape))

try:
    for name,preset in FRAME_CASES.items():
        bases=[replace(preset,KeystoneEnabled=True)]
        bases += [replace(preset,PlateDesign='2 plates',ArmBracesEnabled=True,TwoPlateArmPosition=pos,StandoffHeight=30)
                  for pos in TWO_PLATE_ARM_POSITIONS]
        for base in bases:
            for fpv in (False,True):
                p=replace(base,FPVEnabled=fpv)
                on=build_shapes(p);off=build_shapes(replace(p,StrapSlotsEnabled=False))
                carrier=stack_mounting_role(p);shape=off[carrier];tag=name+'/'+carrier+'/'+p.TwoPlateArmPosition+'/'+str(fpv)
                check(shape.isValid() and len(shape.Solids)==1,tag+': one connected FC carrier')
                if carrier=='ArmClampPlate':
                    check(off['FrontArmBrace'].isNull() and off['RearArmBrace'].isNull(),tag+': old pair omitted')
                    check('ArmClampPlate' in carbon_roles(p),tag+': one clamp included in mass and exports')
                floor=shape.BoundBox.ZMin
                lower=min(off[r].BoundBox.ZMin for r in physical_roles(p))-.1
                for pt in stack_holes(p):
                    check(circle_at(off['BottomPlate'],pt,3),tag+': exact 6 mm bottom access hole')
                    check(circle_at(shape,pt,1.6),tag+': exact normal stack mounting bore in carrier')
                    probe=cylinder(*pt,2.95,lower,floor-lower-.01)
                    for role in physical_roles(p):
                        check(probe.common(off[role]).Volume<1e-6,tag+': service access clears '+role)
                for role in physical_roles(p):
                    if role!=carrier:
                        check(shape.common(off[role]).Volume<1e-6,tag+': carrier clears '+role)
                    check(off['StackEnvelope'].common(off[role]).Volume<1e-6,tag+': stack sits above carrier and clears '+role)
                check(abs(off['StackEnvelope'].BoundBox.ZMin-stack_reference_z(p))<1e-7,tag+': reference follows mounting deck')
                expected=4*((p.StrapSlotLength-p.StrapSlotWidth)*p.StrapSlotWidth+math.pi*(p.StrapSlotWidth/2)**2)*p.TopThickness
                check(abs(off['TopPlate'].Volume-on['TopPlate'].Volume-expected)<1e-5,tag+': exact volume restored by removing four slots')
                for a,b,r in strap_slots(p):
                    point=App.Vector((a[0]+b[0])/2,(a[1]+b[1])/2,plate_levels(p)['top_z']+p.TopThickness/2)
                    check(not on['TopPlate'].isInside(point,1e-7,True) and off['TopPlate'].isInside(point,1e-7,True),tag+': strap opening toggles at actual location')
                if fpv:
                    for mount in camera_mounts(p):
                        x=sum(mount['plate_x'])/2
                        for y in mount['tabs_y']:
                            check(not off['TopPlate'].isInside(App.Vector(x,y,plate_levels(p)['top_z']+1),1e-7,True),tag+': camera tabs retained with straps disabled')
    doc=App.newDocument('RotorForgeStackClamp');settings=create_frame(doc=doc)
    variants=[replace(FPV_CASES['5-inch FPV Deadcat'],PlateDesign='2 plates',ArmBracesEnabled=True,
                      TwoPlateArmPosition='Above bottom plate',StandoffHeight=30,StrapSlotsEnabled=slots) for slots in (True,False)]
    variants += [replace(Parameters(),KeystoneEnabled=True,StrapSlotsEnabled=False),
                 replace(variants[-1],TwoPlateArmPosition='Below bottom plate')]
    for i,p in enumerate(variants):
        update_frame(settings,p);parts=component_objects(settings)
        check(settings.getTypeIdOfProperty('StrapSlotsEnabled')=='App::PropertyBool','Native strap switch uses Boolean property')
        folder=export_package(settings,output);report['export_folders'].append(str(folder))
        info=json.loads((folder/'ExportInfo.json').read_text())
        check(info['strap_slots_enabled']==p.StrapSlotsEnabled and len(info['strap_slots'])==(4 if p.StrapSlotsEnabled else 0),'Export records strap choice and geometry')
        check(info['stack']['mounting_plate']==stack_mounting_role(p) and info['stack']['bottom_hole_diameter_mm']==6,'Export records FC carrier and service access')
        check(len(info['arm_mounting']['connecting_plates'])==(1 if p.PlateDesign=='2 plates' else 0),'Export lists one combined clamp')
        check(not any((folder/'CuttingProfiles'/(r+'.dxf')).exists() for r in ('FrontArmBrace','RearArmBrace')),'Old clamp pair omitted from cutting files')
        if p.PlateDesign=='2 plates':
            check((folder/'CuttingProfiles/ArmClampPlate.dxf').exists(),'Single clamp cutting profile included')
        rows=list(csv.DictReader((folder/'PartsList.csv').open()))
        check(next(r['Quantity'] for r in rows if r['Part']=='FC stack mounting bolts')=='4','Four independent stack fasteners in BOM')
        step=Part.read(str(folder/'FrameAssembly.step'))
        check(step.isValid() and len(step.Solids)==len(carbon_roles(p))+4,'STEP contains one active clamp and selected hardware')
        check(abs(settings.CarbonMassGrams-sum(build_shapes(p)[r].Volume for r in carbon_roles(p))*p.CarbonDensity/1000)<1e-6,'Mass follows actual clamp and strap choice')
        path=output/f'StackClamp_{i}.FCStd';doc.saveAs(str(path));name=settings.Name;App.closeDocument(doc.Name)
        doc=App.openDocument(str(path));settings=doc.getObject(name);doc.recompute()
        check(read_parameters(settings)==p,'New stack and strap settings persist on native reopen')
    doc.UndoMode=1;before=read_parameters(settings);update_frame(settings,replace(before,StrapSlotsEnabled=True));doc.undo();doc.recompute()
    check(read_parameters(settings)==before,'Undo restores strap choice')
    legacy=App.openDocument(str(Path(__file__).parent/'fixtures/Legacy_0.7_Clamps.FCStd'))
    old=legacy.getObject('FrameParameters');update_frame(old,read_parameters(old));parts=component_objects(old)
    check(not parts['ArmClampPlate'].Shape.isNull(),'Version 0.7 gains one combined clamp')
    check(all(parts[r].Shape.isNull() for r in ('FrontArmBrace','RearArmBrace')),'Version 0.7 pair geometry cleared')
    check(read_parameters(old).StrapSlotsEnabled,'Older documents retain strap slots by default')
    report['status']='passed'
except Exception:
    report['status']='failed';report['error']=traceback.format_exc()
finally:
    for d in list(App.listDocuments().values()):App.closeDocument(d.Name)
    (output/'test_report.json').write_text(json.dumps(report,indent=2))
