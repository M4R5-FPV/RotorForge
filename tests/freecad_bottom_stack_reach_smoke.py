"""Explicit rear body dimensions, arm tabs, native migration and exports."""
from pathlib import Path
from dataclasses import replace
import importlib.util,json,os,sys,traceback
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import FreeCAD as App
import Part
from freecad.rotorforge.parameters import Parameters,bottom_bounds,bottom_body_bounds,plate_holes,arm_layouts
from freecad.rotorforge.geometry import build_shapes,carbon_roles,profiled_plate,cylinder
from freecad.rotorforge.document import create_frame,read_parameters,update_frame
from freecad.rotorforge.exporters import export_package
from test_mid_follow import matched_mid
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[],'configurations':[],'migrated_configurations':0}
def check(ok,label):
    if not ok:raise AssertionError(label)
    report['checks'].append(label)
def footprint(shape,z,h):
    top=max((f for f in shape.Faces if f.normalAt(0,0).z>.999),key=lambda f:f.CenterOfMass.z).copy()
    top.translate(App.Vector(0,0,z-top.CenterOfMass.z));return top.extrude(App.Vector(0,0,h))
try:
    oldpath=Path(os.environ['ROTORFORGE_PREVIOUS_SOURCE'])
    spec=importlib.util.spec_from_file_location('rotorforge_previous',oldpath/'__init__.py',submodule_search_locations=[str(oldpath)])
    pkg=importlib.util.module_from_spec(spec);sys.modules[spec.name]=pkg;spec.loader.exec_module(pkg)
    from rotorforge_previous.parameters import Parameters as OldParameters
    from rotorforge_previous.geometry import build_shapes as old_build
    for layout in ('True X','Stretched X','Deadcat'):
        for offset in (-4,0,4):
            baseline=None
            for reach in (26,32,38):
                p=matched_mid(Layout=layout,StackOffsetY=offset,BottomBodyRearReach=reach);shapes=build_shapes(p)
                tag=f'{layout}/{offset}/{reach}';rear,front=bottom_body_bounds(p)
                check(rear==offset-reach,tag+': exact stack-referenced edge')
                main=profiled_plate(p,'BottomPlate',p.BodyWidth,rear,front,p.CornerRadius,0,p.BottomThickness)
                check(abs(main.BoundBox.YMin-rear)<1e-7,tag+': exact CAD body edge')
                roots=[footprint(shapes['Arm'+a['name']],0,p.BottomThickness) for a in arm_layouts(p) if a['root'][1]<0]
                extension=shapes['BottomPlate'].cut(main)
                check(extension.Volume<1e-6 or extension.cut(Part.makeCompound(roots)).Volume<1e-6,tag+': tabs stay within rear arm footprints')
                for role in carbon_roles(p):
                    check(shapes[role].isValid() and len(shapes[role].Solids)==1,tag+': connected '+role)
                    if baseline is not None and role!='BottomPlate':check(shapes[role].cut(baseline[role]).Volume+baseline[role].cut(shapes[role]).Volume<1e-5,tag+': reach leaves '+role)
                for point,radius,name in plate_holes(p,'BottomPlate'):
                    ring=cylinder(*point,radius+p.MinimumWeb,0,p.BottomThickness).cut(cylinder(*point,radius,-.1,p.BottomThickness+.2))
                    check(abs(ring.common(shapes['BottomPlate']).Volume-ring.Volume)<1e-5,tag+': full support '+name)
                if baseline is None:baseline=shapes
                else:check(baseline['BottomPlate'].cut(shapes['BottomPlate']).Volume<1e-6,tag+': longer body fills central cutout')
                report['configurations'].append(tag);print('STACK REACH',tag,flush=True)
    for oldp in [OldParameters(Layout=l,Wheelbase=270) for l in ('True X','Stretched X','Deadcat')]+[
        OldParameters.from_dict({k:v for k,v in matched_mid().to_dict().items() if k!='BottomBodyRearReach'}),
        OldParameters(PlateDesign='2 plates'),OldParameters(PlateDesign='2 plates',TwoPlateArmPosition='Above bottom plate',ArmBracesEnabled=True),
        OldParameters(FPVEnabled=True)]:
        p=Parameters.from_dict(oldp.to_dict());now=build_shapes(p);old=old_build(oldp)
        for role in carbon_roles(p):check(now[role].cut(old[role]).Volume+old[role].cut(now[role]).Volume<1e-5,'Migrated '+oldp.Layout+'/'+oldp.PlateDesign+': unchanged '+role)
        report['migrated_configurations']+=1
    for reach in (20,70):
        p=matched_mid(BottomBodyRearReach=reach);s=build_shapes(p)
        check(s['BottomPlate'].isValid(),'Valid explicit body reach '+str(reach))
        if reach==70:check(s['BottomPlate'].BoundBox.YMin==-70,'Automatic outer limit includes a long body')
    p=matched_mid(BottomBodyRearReach=37,StackOffsetY=5);settings=create_frame(p);doc=settings.Document
    check(settings.getTypeIdOfProperty('BottomBodyRearReach')=='App::PropertyLength','Native body reach is a length')
    path=out/'Example_StackReferencedBottom_3_plates.FCStd';doc.saveAs(str(path));App.closeDocument(doc.Name)
    doc=App.openDocument(str(path));settings=doc.getObject('FrameParameters');doc.recompute();doc.UndoMode=1
    check(read_parameters(settings)==p and settings.Status.startswith('Valid'),'Native new dimension persists')
    update_frame(settings,replace(p,BottomBodyRearReach=29));doc.undo();doc.recompute();check(read_parameters(settings)==p,'Undo restores the body reach')
    folder=export_package(settings,out/'exports');info=json.loads((folder/'ExportInfo.json').read_text())
    check(info['bottom_rear_tabs']['body_rear_datum']=='FC stack centre','Export records the stack datum')
    check(info['bottom_rear_tabs']['body_rear_reach_mm']==37 and info['bottom_rear_tabs']['body_bounds_mm'][0]==-32,'Export records exact body edge')
    check(Part.read(str(folder/'FrameAssembly.step')).isValid(),'STEP assembly reimports')
    for ext in ('dxf','svg'):check((folder/'CuttingProfiles'/('BottomPlate.'+ext)).stat().st_size>100,'Bottom cutting '+ext)
    App.closeDocument(doc.Name)
    olddoc=App.openDocument(str(Path(__file__).resolve().parents[1]/'examples/Example_ArmMatchedBottom_3_plates.FCStd'))
    settings=olddoc.getObject('FrameParameters');p=read_parameters(settings);before=build_shapes(p)['BottomPlate']
    update_frame(settings,p)
    check('BottomBodyRearReach' in settings.PropertiesList,'Older native gains the new control')
    check(read_parameters(settings)==p and before.cut(build_shapes(read_parameters(settings))['BottomPlate']).Volume<1e-6,'Older native preserves its outline')
    App.closeDocument(olddoc.Name);report['status']='passed'
except Exception:report.update(status='failed',error=traceback.format_exc());print(report['error'],flush=True)
finally:
    for doc in list(App.listDocuments().values()):App.closeDocument(doc.Name)
    (out/'test_report.json').write_text(json.dumps(report,indent=2));print('BOTTOM STACK REACH',report['status'],len(report['checks']),flush=True)
