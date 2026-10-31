"""Rear bottom clamps: arm footprints, bores, original parts and exports."""
from dataclasses import replace
from pathlib import Path
import importlib.util,json,math,os,sys,traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import FreeCAD as App
import Part
from freecad.rotorforge.parameters import Parameters,arm_layouts,bottom_body_bounds,plate_holes,plate_levels
from freecad.rotorforge.geometry import build_shapes,carbon_roles,profiled_plate,cylinder,flat_plate_shape
from freecad.rotorforge.document import create_frame,read_parameters,update_frame
from freecad.rotorforge.exporters import export_package,profile_entities
from test_mid_follow import matched_mid
from test_root_adjustments import wide
from frame_cases import FRAME_CASES,FPV_CASES

out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[],'configurations':[],'removed_area_mm2':[]}
def check(ok,label):
    if not ok:raise AssertionError(label)
    report['checks'].append(label)
def footprint(shape,z,height):
    top=max((f for f in shape.Faces if f.normalAt(0,0).z>.999),key=lambda f:f.CenterOfMass.z).copy()
    top.translate(App.Vector(0,0,z-top.CenterOfMass.z));return top.extrude(App.Vector(0,0,height))
try:
    oldpath=Path(os.environ['ROTORFORGE_PREVIOUS_SOURCE'])
    spec=importlib.util.spec_from_file_location('rotorforge_previous',oldpath/'__init__.py',submodule_search_locations=[str(oldpath)])
    pkg=importlib.util.module_from_spec(spec);sys.modules[spec.name]=pkg;spec.loader.exec_module(pkg)
    from rotorforge_previous.parameters import Parameters as OldParameters
    from rotorforge_previous.geometry import build_shapes as old_build
    cases=[]
    for layout in ('True X','Stretched X','Deadcat'):
        for width in (14,24,36):
            for mode in ('Along arm','Custom coordinates'):
                cases.append((f'{layout}/{width}/{mode}',matched_mid(Layout=layout,ArmRootWidth=width,RootBoltLayout=mode)))
        for width in (14,24):cases.append((f'{layout}/{width}/Independent',matched_mid(Layout=layout,ArmRootWidth=width,ArmRootFit='Independent',RootExtension=8,KeystoneEnabled=False)))
        cases.append((layout+'/offset pair',matched_mid(Layout=layout,RootBolt1X=-5,RootBolt1Y=-2,RootBolt2X=5,RootBolt2Y=2)))
        for position in ('Above bottom plate','Below bottom plate'):
            for key in (False,True):cases.append((layout+'/2 plates/'+position+'/'+str(key),wide(Layout=layout,PlateDesign='2 plates',TwoPlateArmPosition=position,ArmBracesEnabled=True,KeystoneEnabled=key)))
    cases += [('Wide centres',matched_mid(BottomCentreWidth=100,MidCentreWidth=100)),
              ('Custom reaches',matched_mid(BottomReachMode='Custom',BottomRearReach=42,BottomFrontReach=100)),
              ('Zero root shoulder',matched_mid(ArmRootLength=0)),
              ('No key',matched_mid(KeystoneEnabled=False))]
    cases += list(FRAME_CASES.items())+list(FPV_CASES.items())
    shared=wide(BodyWidth=70,TopWidth=70,ArmRootY=25,RootInset=15,RootExtension=50,
        StandoffCount='8 (4 pairs)',StandoffFrontMount='Arm outer hole',StandoffRearMount='Arm outer hole',
        StandoffPair3Mount='Front arm inner hole',StandoffPair4Mount='Rear arm inner hole',KeystoneEnabled=True,StrapSlotsEnabled=False)
    cases.append(('Eight shared standoffs',shared))
    for tag,p in cases:
        shapes=build_shapes(p);old=old_build(OldParameters.from_dict(p.to_dict()));bottom=shapes['BottomPlate'];height=p.BottomThickness
        for role in carbon_roles(p):
            check(shapes[role].isValid() and len(shapes[role].Solids)==1,tag+': connected '+role)
            if role!='BottomPlate' or p.PlateDesign=='2 plates':
                check(shapes[role].cut(old[role]).Volume+old[role].cut(shapes[role]).Volume<1e-5,tag+': unchanged '+role)
        if p.PlateDesign=='3 plates':
            main=profiled_plate(p,'BottomPlate',p.BodyWidth,*bottom_body_bounds(p),p.CornerRadius,0,height)
            roots=[footprint(shapes['Arm'+a['name']],0,height) for a in arm_layouts(p) if a['root'][1]<0]
            check(bottom.cut(main).cut(Part.makeCompound(roots)).Volume<1e-6,tag+': no overhang outside rear arm footprints')
            check(bottom.cut(old['BottomPlate']).Volume<1e-6,tag+': bottom only removes material')
            check(old['BottomPlate'].common(main).cut(bottom).Volume<1e-6,tag+': front and stack body preserved')
            report['removed_area_mm2'].append({'configuration':tag,'area':old['BottomPlate'].cut(bottom).Volume/height})
        for point,radius,name in plate_holes(p,'BottomPlate'):
            ring=cylinder(*point,radius+p.MinimumWeb,0,height).cut(cylinder(*point,radius,-.1,height+.2))
            check(abs(ring.common(bottom).Volume-ring.Volume)<1e-5,tag+': full bearing material '+name)
        entities=profile_entities(flat_plate_shape(bottom,'BottomPlate',p))
        for arm in arm_layouts(p):
            for point in arm['bolts']:
                check(any(e[0]=='CIRCLE' and math.dist((e[1],e[2]),point)<1e-7 and abs(e[3]-p.RootHoleDiameter/2)<1e-7 for e in entities),tag+': complete aligned arm bore')
        report['configurations'].append(tag);print('BOTTOM FOLLOW',tag,flush=True)
    check(any(item['area']>5 for item in report['removed_area_mm2']),'Rear overhanging material is removed')
    p=matched_mid();settings=create_frame(p);doc=settings.Document
    path=out/'Example_ArmMatchedBottom_3_plates.FCStd';doc.saveAs(str(path));App.closeDocument(doc.Name)
    doc=App.openDocument(str(path));settings=doc.getObject('FrameParameters');doc.recompute();doc.UndoMode=1
    check(read_parameters(settings)==p and settings.Status.startswith('Valid'),'Native matched-bottom settings persist')
    update_frame(settings,replace(p,ArmRootWidth=36));doc.undo();doc.recompute();check(read_parameters(settings)==p,'Undo restores the rear arm matching')
    folder=Path(export_package(settings,out/'exports'));info=json.loads((folder/'ExportInfo.json').read_text())
    check(info['bottom_rear_tabs']['profile']=='Clipped to rear arm roots','Export records rear arm matching')
    check(Part.read(str(folder/'FrameAssembly.step')).isValid(),'STEP assembly reimports')
    for ext in ('dxf','svg'):check((folder/'CuttingProfiles'/('BottomPlate.'+ext)).stat().st_size>100,'Bottom manufacturing '+ext)
    App.closeDocument(doc.Name);report['status']='passed'
except Exception:report.update(status='failed',error=traceback.format_exc());print(report['error'],flush=True)
finally:
    for doc in list(App.listDocuments().values()):App.closeDocument(doc.Name)
    (out/'test_report.json').write_text(json.dumps(report,indent=2));print('BOTTOM FOLLOW',report['status'],len(report['checks']),flush=True)
