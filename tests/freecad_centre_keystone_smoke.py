"""FreeCADCmd: widened centres, both two-plate key positions and renamed files."""
from dataclasses import replace
from pathlib import Path
import csv,json,math,os,sys,tempfile,traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from rotorforge import __version__
from freecad.rotorforge.parameters import Parameters, TWO_PLATE_ARM_POSITIONS, arm_layouts, keystone_retainers, plate_levels, bottom_bounds, mid_bounds, top_bounds, stack_holes
from tests.frame_cases import FRAME_CASES, FPV_CASES
from freecad.rotorforge.geometry import build_shapes,carbon_roles,physical_roles,flat_plate_shape,cylinder
from freecad.rotorforge.document import create_frame,update_frame,read_parameters,component_objects
from freecad.rotorforge.exporters import export_package,profile_entities
from freecad.rotorforge.cutouts import encode_patterns

output=Path(os.environ.get('ROTORFORGE_TEST_OUTPUT',tempfile.mkdtemp(prefix='rotorforge-centre-key-')));output.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[],'export_folders':[],'freecad_version':'.'.join(App.Version()[:3])}
def check(ok,message):
    if not ok:raise AssertionError(message)
    report['checks'].append(message)
def circle_at(shape,point,radius):
    return any(e[0]=='CIRCLE' and math.dist((e[1],e[2]),point)<1e-7 and abs(e[3]-radius)<1e-7 for e in profile_entities(shape))

try:
    for name,preset in FRAME_CASES.items():
        for position in TWO_PLATE_ARM_POSITIONS:
            for wide in (False,True):
                p=replace(preset,PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,
                          TwoPlateArmPosition=position,StandoffHeight=35)
                if wide:p=replace(p,BottomCentreWidth=70,ClampCentreWidth=70,TopCentreWidth=64)
                s=build_shapes(p);tag=name+'/'+position+'/'+str(wide);key=s['ArmKeystone']
                check('ArmClampPlate' in carbon_roles(p) and 'ArmKeystone' in carbon_roles(p),tag+': key and clamp coexist')
                check(key.isValid() and len(key.Solids)==1,tag+': one connected carbon key')
                check(abs(key.BoundBox.ZMin-plate_levels(p)['arm_z'])<1e-7 and abs(key.BoundBox.ZLength-p.ArmThickness)<1e-7,tag+': key fills the arm layer')
                check(key.distToShape(s['BottomPlate'])[0]<1e-7,tag+': key seats against the bottom')
                if position.startswith('Above'):
                    check(key.distToShape(s['ArmClampPlate'])[0]<1e-7,tag+': upper clamp captures the key')
                    check(not keystone_retainers(p),tag+': captured key needs no retaining screws')
                else:
                    lower=s['ArmLowerClampPlate']
                    check(lower.distToShape(key)[0]<1e-7,tag+': lower plate captures key')
                    for pt in stack_holes(p):check(circle_at(lower,pt,p.StackAccessDiameter/2),tag+': lower plate full access')
                for arm in arm_layouts(p):
                    check(abs(key.distToShape(s['Arm'+arm['name']])[0]-p.KeystoneClearance)<1e-5,tag+': arm seat '+arm['name'])
                for role in physical_roles(p):
                    if role!='ArmKeystone':check(key.common(s[role]).Volume<1e-6,tag+': key clears '+role)
                for pt in stack_holes(p):
                    probe=cylinder(*pt,p.StackAccessDiameter/2-.05,plate_levels(p)['arm_z']-.1,p.ArmThickness+p.BottomThickness-.01)
                    check(probe.common(key).Volume<1e-7,tag+': FC service access stays clear')
    # Exact centre width, unchanged end width/reach, independently on each plate.
    p=Parameters(FPVEnabled=True,BottomCentreWidth=70,MidCentreWidth=70,TopCentreWidth=64,
                 CentreSectionLength=70,CentreShoulderLength=12,BottomReachMode='Custom',BottomRearReach=45,BottomFrontReach=87,
                 MidReachMode='Custom',MidRearReach=100,TopReachMode='Custom',TopRearReach=101,TopFrontReach=86,StandoffHeight=35)
    shapes=build_shapes(p)
    for role,width,z in (('BottomPlate',70,1),('MidPlate',70,8),('TopPlate',64,plate_levels(p)['top_z']+1)):
        shape=shapes[role]
        check(abs(shape.BoundBox.XLength-width)<1e-7,role+': requested centre width is exact')
        check(shape.isInside(App.Vector(width/2-1,0,z),1e-7,True),role+': extra centre material exists')
        if role!='MidPlate':check(not shape.isInside(App.Vector(width/2-1,75,z),1e-7,True),role+': nose keeps its base width')
        expected={'BottomPlate':bottom_bounds,'MidPlate':mid_bounds,'TopPlate':top_bounds}[role](p)
        check(abs(shape.BoundBox.YMin-expected[0])<1e-7 and (role=='MidPlate' or abs(shape.BoundBox.YMax-expected[1])<1e-7),role+': widening preserves exact body reach and the existing mid arm tabs')
    moved=arm_layouts(p)[0]['root'];kept=arm_layouts(replace(p,ArmRootsFollowCentre=False))[0]['root']
    check(abs(moved[0]-25)<1e-8 and abs(kept[0]-15)<1e-8,'Arm root coupling is optional and follows local centre width')
    asymmetric=replace(FRAME_CASES['5-inch Deadcat'],BottomCentreWidth=70,MidCentreWidth=70,TopCentreWidth=70,
                       CentreSectionLength=50,CentreSectionY=15,KeystoneEnabled=True)
    sa=build_shapes(asymmetric);a=arm_layouts(asymmetric)
    check(abs(a[0]['length']-a[2]['length'])<1e-7,'Deadcat compensates unequal front/rear root widths')
    check(all(sa[r].isValid() for r in carbon_roles(asymmetric)),'Offset centre section builds valid Deadcat parts')
    # A cut in the extra material is permitted; a cut at a retainer is rejected.
    airy=replace(p,CutoutPatterns=encode_patterns([dict(role='BottomPlate',shape='Circle',width=3,x=30,y=0)]))
    check(build_shapes(airy)['BottomPlate'].Volume<shapes['BottomPlate'].Volume,'Airflow can use widened material outside the old outline')
    bad=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,
                   CutoutPatterns=encode_patterns([dict(role='ArmLowerClampPlate',shape='Circle',width=4,x=15.25,y=15.25)]))
    try:build_shapes(bad)
    except ValueError:check(True,'Airflow cannot cut away a stack access passage')
    else:raise AssertionError('Unsafe access cutout accepted')
    # Renamed native project, complete exports and an actual old proxy restore.
    doc=App.newDocument('RotorForgeNew');doc.UndoMode=1;settings=create_frame(p,doc)
    check(any(o.Name=='RotorForge' and o.Label.startswith('RotorForge') for o in doc.Objects),'Frame group uses RotorForge')
    variants=[p,replace(p,PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,ClampCentreWidth=70,BottomRearReach=100,TwoPlateArmPosition='Above bottom plate'),
              replace(p,PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,ClampCentreWidth=70,BottomRearReach=100,TwoPlateArmPosition='Below bottom plate')]
    for index,q in enumerate(variants):
        update_frame(settings,q);folder=export_package(settings,output);report['export_folders'].append(str(folder))
        check(folder.name.startswith('RotorForge_'),'Export folder uses RotorForge')
        info=json.loads((folder/'ExportInfo.json').read_text())
        check(info['centre_sections']['widths_mm']['BottomPlate']==70,'Export records centre dimensions')
        step=Part.read(str(folder/'FrameAssembly.step'))
        check(step.isValid() and len(step.Solids)==len(carbon_roles(q))+4,'STEP includes key, clamp and all physical components')
        if keystone_retainers(q):
            rows=list(csv.DictReader((folder/'MachiningOps.csv').open()))
            check(len(rows)==2 and all(float(r['depth_mm'])==1.4 for r in rows),'Two secondary countersink operations with exact depth')
            stock=list(csv.DictReader((folder/'PartsList.csv').open()))
            check(next(r['Quantity'] for r in stock if r['Part']=='Keystone retaining countersunk bolts')=='2','Retaining hardware is included in BOM')
            check(info['arm_mounting']['keystone'] is not None and len(info['secondary_machining'])==2,'Retainer metadata accompanies the key')
        else:check(not (folder/'MachiningOps.csv').exists(),'No unnecessary countersink operations for captured keys')
        path=output/f'RotorForgeCentre_{index}.FCStd';doc.saveAs(str(path));name=settings.Name;App.closeDocument(doc.Name)
        doc=App.openDocument(str(path));settings=doc.getObject(name);doc.recompute();doc.UndoMode=1
        check(read_parameters(settings)==q,'Centre/key choices survive native reopen')
        check(settings.Proxy.__class__.__module__=='rotorforge.document','Native proxies save the new package name')
    before=read_parameters(settings);update_frame(settings,replace(before,BottomCentreWidth=72,ClampCentreWidth=72));doc.undo();doc.recompute()
    check(read_parameters(settings)==before,'Undo restores centre dimensions')
    settings.Proxy=None
    for obj in component_objects(settings).values():obj.Proxy=None
    update_frame(settings,before)
    check(settings.Proxy.__class__.__module__=='rotorforge.document','Editor update restores a missing parameter proxy')
    check(all(obj.Proxy.__class__.__module__=='rotorforge.document' for obj in component_objects(settings).values()),'Editor update restores missing component proxies')
    path=output/'RotorForgeRestoredProxies.FCStd';doc.saveAs(str(path));name=settings.Name;App.closeDocument(doc.Name)
    doc=App.openDocument(str(path));settings=doc.getObject(name);doc.recompute()
    check(settings.Status.startswith('Valid') and read_parameters(settings)==before,'Restored proxies save and reopen with the same parameters')
    legacy=App.openDocument(str(Path(__file__).parent/'fixtures/Legacy_0.8.FCStd'));old=legacy.getObject('FrameParameters')
    q=read_parameters(old);update_frame(old,q)
    check(str(old.Status).startswith('Valid') and old.GeneratorVersion==__version__,'Old proxy module restores and updates after rename')
    check(old.Proxy.__class__.__module__=='rotorforge.document','Compatibility fixture uses the canonical proxy implementation')
    check(any(o.Label.startswith('RotorForge') for o in legacy.Objects),'Old generated group displays the new name')
    check(q.BottomCentreWidth==0 and q.ClampCentreWidth==0,'Older files keep their original straight profiles')
    report['status']='passed'
except Exception:
    report['status']='failed';report['error']=traceback.format_exc()
finally:
    for doc in list(App.listDocuments().values()):App.closeDocument(doc.Name)
    (output/'test_report.json').write_text(json.dumps(report,indent=2))
    print('ROTORFORGE CENTRE/KEY',report['status'],len(report['checks']),flush=True)
