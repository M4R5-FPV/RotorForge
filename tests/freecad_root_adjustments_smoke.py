"""Exact solids, mounting alignment, old geometry and native custom coordinates."""
from dataclasses import replace
from itertools import combinations
from pathlib import Path
from zipfile import ZipFile
import importlib.util
import json
import os
import sys
import tempfile
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from freecad.rotorforge.parameters import Parameters,arm_layouts,plate_levels,stack_holes,plate_holes,stack_mounting_role,standoff_layouts
from freecad.rotorforge.arm_roots import ROOT_PROFILE_FIELDS,arm_local_point,stem_interior_distance,fitted_roots
from freecad.rotorforge.geometry import build_shapes,carbon_roles,physical_roles,cylinder,arm_stem,flat_plate_shape
from freecad.rotorforge.document import create_frame,update_frame,read_parameters
from freecad.rotorforge.exporters import export_package,profile_entities
from test_root_adjustments import wide

out=Path(os.environ.get('ROTORFORGE_TEST_OUTPUT',tempfile.mkdtemp(prefix='rotorforge-roots-')));out.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[],'configurations':[],'examples':[]}
def check(ok,label):
    if not ok:raise AssertionError(label)
    report['checks'].append(label)

def verify(p,tag):
    shapes=build_shapes(p);arms=arm_layouts(p);levels=plate_levels(p)
    for role in carbon_roles(p):check(shapes[role].isValid() and len(shapes[role].Solids)==1,tag+' connected '+role)
    for a,b in combinations(arms,2):
        x,y=shapes['Arm'+a['name']],shapes['Arm'+b['name']]
        check(x.common(y).Volume<1e-6,tag+' no arm overlap')
    for arm in arms:
        stem=arm_stem(p,arm,levels['arm_z'],p.ArmThickness)
        check(stem.isValid() and len(stem.Solids)==1,tag+' valid taper '+arm['name'])
        # Compare analytic edge clearance with the actual uncut boundary.
        face=max((f for f in stem.Faces if abs(f.normalAt(0,0).z)>.999),key=lambda f:f.CenterOfMass.z)
        for t,s in ((0,10),(10,12),(25,9.5),(45,6),(-25,0),(37,8)):
            pt=arm_local_point(arm,t,s)
            actual=face.OuterWire.distToShape(Part.Vertex(App.Vector(*pt,face.CenterOfMass.z)))[0]
            check(abs(actual-abs(stem_interior_distance(p,arm,pt)))<1e-6,tag+' exact taper distance')
        entities=profile_entities(flat_plate_shape(shapes['Arm'+arm['name']],'Arm'+arm['name'],p))
        for point in arm['bolts']:
            check(any(e[0]=='CIRCLE' and math_distance((e[1],e[2]),point)<1e-7 and abs(e[3]-p.RootHoleDiameter/2)<1e-7 for e in entities),tag+' complete custom arm bore')
            for role in ('BottomPlate','MidPlate','ArmClampPlate','ArmLowerClampPlate'):
                if shapes[role].isNull():continue
                matching=[(pt,r) for pt,r,_ in plate_holes(p,role) if math_distance(pt,point)<1e-7]
                if not matching:continue
                z=shapes[role].BoundBox.ZMin;thick=shapes[role].BoundBox.ZLength
                check(shapes[role].common(cylinder(*point,matching[0][1],z-.1,thick+.2)).Volume<1e-6,tag+' aligned '+role)
    if p.KeystoneEnabled:
        for arm in arms:check(abs(shapes['ArmKeystone'].distToShape(shapes['Arm'+arm['name']])[0]-p.KeystoneClearance)<1e-5,tag+' key seats widened root')
    if p.PlateDesign=='3 plates' or p.ArmBracesEnabled:
        carrier=stack_mounting_role(p);low=min(shapes[r].BoundBox.ZMin for r in carbon_roles(p));top=shapes[carrier].BoundBox.ZMin
        for point in stack_holes(p):
            tunnel=cylinder(*point,p.StackAccessDiameter/2,low-.1,top-low+.1)
            for role in carbon_roles(p):
                if role!=carrier:check(shapes[role].common(tunnel).Volume<1e-6,tag+' clear stack service tunnel')
    for stand in standoff_layouts(p):
        if stand['shared_arm']:
            check(any(math_distance(stand['point'],pt)<1e-7 for a in arms for pt in a['bolts']),tag+' shared standoff follows bolt')
    report['configurations'].append(tag);print('ROOT ADJUSTMENTS',tag,flush=True)
    return shapes

def math_distance(a,b):return ((a[0]-b[0])**2+(a[1]-b[1])**2)**.5

try:
    for layout in (() if os.environ.get('ROTORFORGE_SKIP_MATRIX') else ('True X','Stretched X','Deadcat')):
        for design,position in [('3 plates','Below bottom plate'),('2 plates','Above bottom plate'),('2 plates','Below bottom plate')]:
            for key in (False,True):
                p=wide(Layout=layout,PlateDesign=design,TwoPlateArmPosition=position,ArmBracesEnabled=design=='2 plates',KeystoneEnabled=key,ArmJointClearance=.2)
                verify(p,'/'.join((layout,design,position,str(key))))
    independent=Parameters(ArmRootWidth=24,ArmRootLength=15,ArmRootTaperLength=20,Wheelbase=270,
        RootBoltLayout='Custom coordinates',RootBolt1X=-5,RootBolt2X=5,RootBolt1Y=-2,RootBolt2Y=2,
        StandoffHeight=35,StandoffLength=105,BodyLength=135,TopLength=135,BodyWidth=70,TopWidth=70,RootInset=15)
    for key in (False,True):verify(replace(independent,KeystoneEnabled=key),'Independent/'+str(key))
    shared=wide(BodyWidth=70,TopWidth=70,ArmRootY=25,RootInset=15,RootExtension=50,
        StandoffCount='8 (4 pairs)',StandoffFrontMount='Arm outer hole',StandoffRearMount='Arm outer hole',
        StandoffPair3Mount='Front arm inner hole',StandoffPair4Mount='Rear arm inner hole',KeystoneEnabled=True,StrapSlotsEnabled=False)
    verify(shared,'Eight shared custom arm mounts')
    verify(wide(RootBoltLayout='Along arm',ArmRootLength=0,ArmRootTaperLength=20),'Wide root with zero shoulder reach')
    for p in (wide(KeystoneEnabled=True),wide(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True)):
        settings=create_frame(p);doc=settings.Document;doc.UndoMode=1
        for name in ('RootBolt1Y','RootBolt1X','RootBolt2Y','RootBolt2X'):
            check(settings.getTypeIdOfProperty(name)=='App::PropertyDistance','Signed native property '+name)
        filename=out/('Example_WideRoots_CustomBolts_'+('3_plates' if p.PlateDesign=='3 plates' else '2_plates')+'.FCStd')
        doc.saveAs(str(filename));App.closeDocument(doc.Name)
        doc=App.openDocument(str(filename));settings=doc.getObject('FrameParameters');doc.recompute();doc.UndoMode=1
        check(read_parameters(settings)==p,'Native signed custom pattern persists')
        update_frame(settings,replace(p,ArmRootWidth=26,RootBolt1X=-3.8));doc.undo();doc.recompute()
        check(read_parameters(settings)==p,'Undo restores root width and custom pattern')
        folder=Path(export_package(settings,out/'exports'))
        metadata=json.loads((folder/'ExportInfo.json').read_text())
        check(metadata['arm_mounting']['root_profile']['width_mm']==24,'Export records root width')
        check(metadata['arm_mounting']['bolt_coordinates']['reference_offsets_xy_mm']==[[-4,0],[4,0]],'Export records frame X/Y offsets')
        shape=Part.read(str(folder/'FrameAssembly.step'))
        check(shape.isValid() and len(shape.Solids)==len(physical_roles(p))-1+len(standoff_layouts(p)),'STEP reimports with every physical part')
        App.closeDocument(doc.Name);report['examples'].append(str(filename))
    earlier=Path(__file__).resolve().parents[1]/'examples/Example_CompactKeystone_3_plates.FCStd'
    doc=App.openDocument(str(earlier));settings=doc.getObject('FrameParameters');doc.recompute()
    old=read_parameters(settings)
    check(old.ArmRootWidth==0 and old.RootBoltLayout=='Along arm','Older native document gets compatible defaults')
    update_frame(settings,wide(KeystoneEnabled=True))
    check(read_parameters(settings)==wide(KeystoneEnabled=True),'Older native document accepts signed custom controls')
    App.closeDocument(doc.Name)
    previous_archive=os.environ.get('ROTORFORGE_PREVIOUS_ARCHIVE')
    if previous_archive:
        name='Example_WideRoots_CustomBolts_3_plates.FCStd'
        with ZipFile(previous_archive) as archive:(out/'Earlier_CustomBolts.FCStd').write_bytes(archive.read('RotorForge/examples/'+name))
        doc=App.openDocument(str(out/'Earlier_CustomBolts.FCStd'));settings=doc.getObject('FrameParameters');doc.recompute()
        migrated=read_parameters(settings)
        check(all(n in settings.PropertiesList for n in ('RootBolt1X','RootBolt1Y','RootBolt2X','RootBolt2Y')),'Earlier custom native gains frame coordinate properties')
        check(not any(n in settings.PropertiesList for n in ('RootBolt1Along','RootBolt1Across','RootBolt2Along','RootBolt2Across')),'Earlier native retires arm coordinate properties')
        arm=arm_layouts(migrated)[0];ux,uy=arm['unit'];rx,ry=arm['root']
        for actual,(t,s) in zip(arm['bolts'],((-4,2.5),(4,-2.5))):
            check(math_distance(actual,(rx+t*ux-s*uy,ry+t*uy+s*ux))<1e-7,'Migration retains earlier front-right bolt position')
        check(settings.Status.startswith('Valid'),'Earlier custom native remains valid')
        App.closeDocument(doc.Name)
    previous=os.environ.get('ROTORFORGE_PREVIOUS_MODULE')
    if previous:
        path=Path(previous);spec=importlib.util.spec_from_file_location('rotorforge_previous',path/'__init__.py',submodule_search_locations=[str(path)])
        package=importlib.util.module_from_spec(spec);sys.modules[spec.name]=package;spec.loader.exec_module(package)
        from rotorforge_previous.parameters import Parameters as OldParameters
        from rotorforge_previous.geometry import build_shapes as old_build
        cases=[Parameters(),Parameters(KeystoneEnabled=True),wide(ArmRootWidth=0,RootBoltLayout='Along arm',KeystoneEnabled=True)]
        cases += [Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,TwoPlateArmPosition=pos) for pos in ('Above bottom plate','Below bottom plate')]
        cases += [Parameters(Layout=layout,Wheelbase=270) for layout in ('Stretched X','Deadcat')]
        for i,p in enumerate(cases):
            before=old_build(OldParameters.from_dict({k:v for k,v in p.to_dict().items() if k not in ROOT_PROFILE_FIELDS}));after=build_shapes(p)
            for role in carbon_roles(p):check(before[role].cut(after[role]).Volume+after[role].cut(before[role]).Volume<1e-5,'Legacy geometry preserved '+str(i)+'/'+role)
    report['status']='passed'
except Exception:
    report['status']='failed';report['error']=traceback.format_exc();print(report['error'],flush=True)
finally:
    for doc in list(App.listDocuments().values()):App.closeDocument(doc.Name)
    (out/'test_report.json').write_text(json.dumps(report,indent=2));print('ROOT ADJUSTMENTS',report['status'],len(report['checks']),flush=True)
