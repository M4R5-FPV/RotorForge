"""FreeCADCmd: shared arm mounts, Deadcat compensation, tabbed camera plates."""
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
import Mesh
from rotorforge import __version__
from freecad.rotorforge.parameters import Parameters, PLATE_DESIGNS, STANDOFF_COUNTS, arm_layouts, standoff_layouts, plate_levels, validate
from tests.frame_cases import FRAME_CASES, FPV_CASES
from freecad.rotorforge.geometry import build_shapes,carbon_roles,physical_roles,flat_plate_shape,cylinder
from freecad.rotorforge.fpv import CAMERA_ROLES,VTX_PATTERNS,camera_mounts
from freecad.rotorforge.document import create_frame,update_frame,read_parameters,component_objects
from freecad.rotorforge.exporters import export_package,profile_entities
from freecad.rotorforge.view import front_view_rotation

output=Path(os.environ.get('ROTORFORGE_TEST_OUTPUT',tempfile.mkdtemp(prefix='rotorforge-assembly-')))
output.mkdir(parents=True,exist_ok=True)
report={'status':'running','freecad_version':'.'.join(App.Version()[:3]),'checks':[],'export_folders':[]}

def check(condition,message):
    if not condition: raise AssertionError(message)
    report['checks'].append(message)

def top_face(shape):
    return max((f for f in shape.Faces if abs(f.normalAt(0,0).z)>.999999),key=lambda f:f.CenterOfMass.z)

def motor_bore(shape,p):
    return next((e[1],e[2]) for e in profile_entities(shape) if e[0]=='CIRCLE' and abs(e[3]-p.MotorCenterDiameter/2)<1e-7)

try:
    eye=front_view_rotation().multVec(App.Vector(0,0,1))
    check(eye.y>0 and eye.z>0,'Initial view is on the +Y front side')
    for name,preset in FRAME_CASES.items():
        for mode in PLATE_DESIGNS:
            for count,number in zip(STANDOFF_COUNTS,(4,6,8)):
                p=replace(preset,FPVEnabled=True,PlateDesign=mode,StandoffCount=count,StandoffHeight=30)
                shapes=build_shapes(p);tag=f'{name}/{mode}/{number}'
                check(all(shapes[r].isValid() and len(shapes[r].Solids)==1 for r in carbon_roles(p)),tag+': connected frame and camera plates')
                check(len(top_face(shapes['BottomPlate']).Wires)==(17+sum(s['mount']!='Mid plate' for s in standoff_layouts(p)) if mode=='3 plates' else 25+number),tag+': base holes and four tab slots')
                check(len(top_face(shapes['TopPlate']).Wires)==9+number,tag+': top holes, straps, and four tab slots')
                if mode=='3 plates':
                    check(len(top_face(shapes['MidPlate']).Wires)==(23 if number==4 else 25),tag+': only VTX and mounting holes in mid')
                for mount in camera_mounts(p):
                    role=mount['role'];shape=shapes[role]
                    check(abs(shape.BoundBox.ZMin)<1e-7 and abs(shape.BoundBox.ZMax-(plate_levels(p)['top_z']+p.TopThickness))<1e-7,
                          tag+': side plate reaches through bottom and top')
                    flat=flat_plate_shape(shape,role)
                    check(abs(flat.BoundBox.ZLength-p.CameraBracketThickness)<1e-7,tag+': side plate flattens at correct stock thickness')
                    check(any(e[0]=='CIRCLE' and abs(e[3]-p.CameraSideHoleDiameter/2)<1e-7 for e in profile_entities(flat)),
                          tag+': camera screw bore included in flat cutting profile')
                    x=sum(mount['plate_x'])/2
                    for y in mount['tabs_y']:
                        for horizontal,z in (('BottomPlate',p.BottomThickness/2),('TopPlate',plate_levels(p)['top_z']+p.TopThickness/2)):
                            point=App.Vector(x,y,z)
                            check(shape.isInside(point,1e-7,True),tag+': tongue occupies '+horizontal+' thickness')
                            check(not shapes[horizontal].isInside(point,1e-7,True),tag+': matching slot in '+horizontal)
                    for horizontal in ('BottomPlate','TopPlate'):
                        check(shape.common(shapes[horizontal]).Volume<1e-6,tag+': no side plate overlap with '+horizontal)
                        check(shape.distToShape(shapes[horizontal])[0]<1e-6,tag+': side plate shoulder seated against '+horizontal)
                for name_ref in ('CameraEnvelope','VTXEnvelope'):
                    for role in physical_roles(p):
                        check(shapes[name_ref].common(shapes[role]).Volume<1e-6,tag+': '+name_ref+' clears '+role)
    for name,preset in FRAME_CASES.items():
        for mode in PLATE_DESIGNS:
            for mounting in ('Arm inner hole','Arm outer hole','all eight'):
                p=replace(preset,PlateDesign=mode,TopWidth=50,StandoffFrontMount='Arm outer hole' if mounting=='all eight' else mounting,
                          StandoffRearMount='Arm outer hole' if mounting=='all eight' else mounting)
                if mounting=='all eight':
                    p=replace(p,StandoffCount=STANDOFF_COUNTS[2],StandoffPair3Mount='Rear arm inner hole',StandoffPair4Mount='Front arm inner hole')
                shapes=build_shapes(p);stands=standoff_layouts(p);tag=f'{name}/{mode}/{mounting}'
                check(len(top_face(shapes['BottomPlate']).Wires)==13,tag+': shared bottom holes cut once')
                if mode=='3 plates':check(len(top_face(shapes['MidPlate']).Wires)==13,tag+': shared mid holes cut once')
                check(len(shapes['Standoffs'].Solids)==len(stands),tag+': one tube per mount')
                lower=0 if mode=='3 plates' else -p.ArmThickness
                upper=plate_levels(p)['top_z']+p.TopThickness
                for stand in stands:
                    check(stand['shared_arm'] is not None,tag+': exact arm bolt alignment')
                    probe=cylinder(*stand['point'],p.RootHoleDiameter/2-.05,lower-.1,upper-lower+.2)
                    for role in physical_roles(p):
                        check(probe.common(shapes[role]).Volume<1e-6,tag+': clear coaxial bolt path through '+role)
                    solid=min(shapes['Standoffs'].Solids,key=lambda s:math.dist((s.CenterOfMass.x,s.CenterOfMass.y),stand['point']))
                    check(abs(solid.BoundBox.ZMin-plate_levels(p)['deck_z'])<1e-7,tag+': standoff rests above arm sandwich')
    p=Parameters(TopWidth=50)
    bolt=arm_layouts(p)[0]['bolts'][1]
    aligned=replace(p,StandoffWidth=2*bolt[0],StandoffLength=2*bolt[1])
    check(not validate(aligned)[0],'Manually positioned coaxial mounts are accepted')
    for bad in (replace(aligned,StandoffWidth=aligned.StandoffWidth+.01),replace(aligned,StandoffHoleDiameter=2.2)):
        try:build_shapes(bad)
        except ValueError:check(True,'Misaligned or incompatible shared mount rejected')
        else:raise AssertionError('Invalid shared mount accepted')
    previous=None
    for spread in (1,1.1,1.2,1.3,1.4):
        p=replace(FPV_CASES['5-inch FPV Deadcat'],FrontSpread=spread)
        shapes=build_shapes(p)
        fr=motor_bore(shapes['ArmFrontRight'],p);fl=motor_bore(shapes['ArmFrontLeft'],p)
        rr=motor_bore(shapes['ArmRearRight'],p);rl=motor_bore(shapes['ArmRearLeft'],p)
        check(fr[1]>0 and fl[1]>0 and rr[1]<0 and rl[1]<0,f'{spread}: physical front/rear bores use correct ends')
        check(abs(math.dist(fr,rl)-p.Wheelbase)<1e-7 and abs(math.dist(fl,rr)-p.Wheelbase)<1e-7,f'{spread}: actual motor diagonals retained')
        rear=next(a for a in arm_layouts(p) if a['name']=='RearRight')
        length=math.dist(rr,rear['root'])
        if previous:check(length>previous,f'{spread}: actual rear arm gets longer with front spread')
        previous=length
        check(shapes['CameraEnvelope'].BoundBox.YMin>0 and shapes['VTXEnvelope'].BoundBox.YMax<0,f'{spread}: camera and VTX stay at correct ends')
    for width in (14,19,20,22,28):
        for mode in PLATE_DESIGNS:
            p=replace(Parameters(),FPVEnabled=True,PlateDesign=mode,CameraWidth=width,CameraHeight=width,StandoffHeight=35)
            shapes=build_shapes(p)
            check(shapes['CameraEnvelope'].isValid(),f'{width}/{mode}: camera fits captured side plates')
    for tilt in (0,30,45):
        p=replace(Parameters(),FPVEnabled=True,CameraMountMode="Fixed",CameraSideBoltSpacing=8,CameraTilt=tilt,StandoffHeight=35)
        shapes=build_shapes(p)
        for role in CAMERA_ROLES:
            holes=[f.Surface for f in shapes[role].Faces if isinstance(f.Surface,Part.Cylinder) and abs(f.Surface.Axis.x)>.999]
            check(len(holes)==2,f'{tilt}: actual two-screw camera side pattern')
            check(abs(math.dist((holes[0].Center.y,holes[0].Center.z),(holes[1].Center.y,holes[1].Center.z))-8)<1e-7,
                  f'{tilt}: exact camera screw pitch')
    doc=App.newDocument('RotorForgeAssemblyTest');settings=create_frame(doc=doc)
    original_mass=settings.CarbonMassGrams
    for mode in PLATE_DESIGNS:
        for pattern in VTX_PATTERNS:
            p=replace(FPV_CASES['5-inch FPV Deadcat'],PlateDesign=mode,VTXPattern=pattern,StandoffHeight=30)
            if pattern==VTX_PATTERNS[0]:p=replace(p,VTX20HoleDiameter=3.2)
            update_frame(settings,p)
            folder=export_package(settings,output);report['export_folders'].append(str(folder))
            loaded=Part.read(str(folder/'FrameAssembly.step'))
            check(loaded.isValid() and len(loaded.Solids)==len(carbon_roles(p))+4,mode+'/'+pattern+': STEP solid count')
            for role in CAMERA_ROLES:
                mesh=Mesh.Mesh(str(folder/'CameraPlates'/(role+'.stl')))
                check(mesh.isSolid() and abs(mesh.BoundBox.ZLength-p.CameraBracketThickness)<1e-6 and abs(mesh.BoundBox.ZMin)<1e-7,
                      role+': flat closed STL at Z=0')
                check((folder/'CuttingProfiles'/(role+'.dxf')).exists(),role+': flat DXF included')
            rows=list(csv.DictReader((folder/'PartsList.csv').open()))
            check(sum(int(r['Quantity']) for r in rows if r['Part'] in ('Arm root bolts','Arm clamp bolts into standoffs'))==8,'Arm hardware counted once')
            check(next(r['Quantity'] for r in rows if r['Part']=='Arm clamp bolts into standoffs')=='4','Shared clamp quantity exported')
            check(all(float(r['Thickness_mm'])==3 for r in rows if r['Part'] in CAMERA_ROLES),'Side plate BOM uses stock thickness')
            check(not any(r['Part']=='Camera bracket mounting bolts' for r in rows),'Obsolete base screws omitted')
            info=json.loads((folder/'ExportInfo.json').read_text())
            check(len(info['fpv']['camera_tab_slots'])==4 and all(s['shared_arm'] for s in info['standoffs']),'Tab and shared mount metadata exported')
            path=output/f'Example_{mode.replace(" ","_")}_{VTX_PATTERNS.index(pattern)}.FCStd'
            name=settings.Name;doc.saveAs(str(path));App.closeDocument(doc.Name)
            doc=App.openDocument(str(path));settings=doc.getObject(name);doc.recompute()
            check(read_parameters(settings)==p,'New mounting settings survive native reopen')
            check(component_objects(settings)['CameraEnvelope'].Shape.BoundBox.YMin>50,'Native tilted camera placement retained')
            check(abs(component_objects(settings)['CameraMountLeft'].Shape.BoundBox.ZMax-(plate_levels(p)['top_z']+p.TopThickness))<1e-7,
                  'Native camera plate upper tabs survive reopen')
    doc.UndoMode=1;update_frame(settings,Parameters())
    check(all(component_objects(settings)[r].Shape.isNull() for r in CAMERA_ROLES),'FPV off removes side plates')
    check(abs(settings.CarbonMassGrams-original_mass)<1e-7,'FPV off restores original carbon mass')
    folder=export_package(settings,output);report['export_folders'].append(str(folder))
    check(not (folder/'CameraPlates').exists(),'Non-FPV export omits camera plate files')
    doc.undo();doc.recompute();check(read_parameters(settings).FPVEnabled,'Undo restores captured camera plates')
    legacy=App.openDocument(str(Path(__file__).resolve().parent/'fixtures/Legacy_0.5.FCStd'))
    old=legacy.getObject('FrameParameters');p=read_parameters(old);update_frame(old,p)
    check(old.GeneratorVersion==__version__,'Version 0.5 document upgrades')
    check(abs(component_objects(old)['CameraMountLeft'].Shape.BoundBox.ZMin)<1e-7,'Legacy L mount replaced by tabbed side plate')
    report['status']='passed'
except Exception:
    report['status']='failed';report['error']=traceback.format_exc();raise
finally:
    (output/'test_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('ROTORFORGE ASSEMBLY TESTS',report['status'],len(report['checks']),str(output),flush=True)
