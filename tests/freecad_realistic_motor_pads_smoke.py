"""Validate exact motor-end solids, original outlines, exports and persistence."""
from dataclasses import replace
from pathlib import Path
import importlib.util,json,math,os,sys,traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from freecad.rotorforge.parameters import Parameters,LAYOUTS,arm_layouts,plate_levels
from freecad.rotorforge.motor_pads import REALISTIC_MOTOR_PAD_SHAPES,MOTOR_PAD_SHAPES,motor_pad_primitives
from freecad.rotorforge.geometry import build_shapes,carbon_roles,cylinder,flat_plate_shape
from freecad.rotorforge.document import create_frame,read_parameters,update_frame,component_objects
from freecad.rotorforge.exporters import export_package,profile_entities

output=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);output.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[],'configurations':[],'original_configurations':0}
def check(ok,label):
    if not ok:raise AssertionError(label)
    report['checks'].append(label)
def verify(p):
    tag='/'.join((p.MotorPadShape,p.Layout,p.PlateDesign,p.TwoPlateArmPosition,str(p.MotorSpacingX),str(p.MotorSpacingY)))
    shapes=build_shapes(p);z=plate_levels(p)['arm_z']
    for role in carbon_roles(p):check(shapes[role].isValid() and len(shapes[role].Solids)==1,tag+': connected '+role)
    for arm in arm_layouts(p):
        role='Arm'+arm['name'];actual=shapes[role];ux,uy=arm['unit'];mx,my=arm['motor']
        for pt in arm['motor_holes']:
            check(actual.common(cylinder(*pt,p.MotorHoleDiameter/2-.02,z-.1,p.ArmThickness+.2)).Volume<1e-6,tag+': open bolt '+role)
            support=cylinder(*pt,p.MotorHoleDiameter/2+p.MinimumWeb,z,p.ArmThickness).cut(cylinder(*pt,p.MotorHoleDiameter/2,z-.1,p.ArmThickness+.2))
            check(abs(support.common(actual).Volume-support.Volume)<1e-5,tag+': full bolt web '+role)
        check(actual.common(cylinder(mx,my,p.MotorCenterDiameter/2-.02,z-.1,p.ArmThickness+.2)).Volume<1e-6,tag+': open centre '+role)
        local=actual.copy();local.translate(App.Vector(-mx,-my,0));local.rotate(App.Vector(),App.Vector(0,0,1),-math.degrees(math.atan2(uy,ux)))
        check(abs(local.BoundBox.XMax-p.MotorPadDiameter/2)<1e-6,tag+': outward nose '+role)
        for cut in (d for d in motor_pad_primitives(p) if d.get('operation')=='cut'):
            x,y=cut['centre'];tool=cylinder(mx+ux*x-uy*y,my+uy*x+ux*y,cut['radius']-.01,z,p.ArmThickness)
            check(actual.common(tool).Volume<1e-6,tag+': edge relief '+role)
    report['configurations'].append(tag);print('Verified '+tag,flush=True)
try:
    for shape in REALISTIC_MOTOR_PAD_SHAPES[:4]:
        for layout in LAYOUTS:
            for design,position in (('3 plates','Below bottom plate'),('2 plates','Below bottom plate'),('2 plates','Above bottom plate')):
                verify(Parameters(MotorPadShape=shape,Layout=layout,Wheelbase=270,PlateDesign=design,TwoPlateArmPosition=position,ArmBracesEnabled=design=='2 plates',StandoffHeight=35))
        for sx,sy in ((16,19),(19,16)):
            verify(Parameters(MotorPadShape=shape,MotorPadDiameter=36,MotorSpacingX=sx,MotorSpacingY=sy))
        p=Parameters(MotorPadShape=shape,Wheelbase=270);settings=create_frame(p);doc=settings.Document
        folder=export_package(settings,output/'exports');info=json.loads((folder/'ExportInfo.json').read_text())
        check(info['motor_pad']['shape']==shape,shape+': export metadata')
        check(Part.read(str(folder/'FrameAssembly.step')).isValid(),shape+': STEP reimport')
        for arm in arm_layouts(p):
            role='Arm'+arm['name'];entities=profile_entities(flat_plate_shape(component_objects(settings)[role].Shape,role))
            check(any(e[0]=='CIRCLE' for e in entities),shape+': analytic motor holes '+role)
            if shape in ('Teardrop','Scalloped shield'):
                radius=p.MotorPadDiameter/2 if shape=='Teardrop' else p.MotorPadCornerRadius
                check(any(e[0]=='ARC' and abs(e[3]-radius)<1e-6 for e in entities),shape+': analytic outline arcs '+role)
            for ext in ('dxf','svg'):check((folder/'CuttingProfiles'/(role+'.'+ext)).stat().st_size>100,shape+': '+ext+' '+role)
        target=output/('Native_'+shape.replace(' ','_')+'.FCStd');doc.saveAs(str(target));App.closeDocument(doc.Name)
        doc=App.openDocument(str(target));settings=doc.getObject('FrameParameters');doc.recompute();doc.UndoMode=1
        check(read_parameters(settings)==p and settings.Status.startswith('Valid'),shape+': native reopen')
        update_frame(settings,replace(p,MotorPadShape='Round'));doc.undo();doc.recompute()
        check(read_parameters(settings)==p,shape+': Undo');App.closeDocument(doc.Name)
    oldpath=Path(os.environ['ROTORFORGE_PREVIOUS_SOURCE'])
    spec=importlib.util.spec_from_file_location('rotorforge_previous',oldpath/'__init__.py',submodule_search_locations=[str(oldpath)])
    oldpkg=importlib.util.module_from_spec(spec);sys.modules[spec.name]=oldpkg;spec.loader.exec_module(oldpkg)
    from rotorforge_previous.parameters import Parameters as OldParameters
    from rotorforge_previous.geometry import build_shapes as old_build
    for shape in MOTOR_PAD_SHAPES[:6]:
        for layout in LAYOUTS:
            p=Parameters(MotorPadShape=shape,Layout=layout,Wheelbase=270);now=build_shapes(p);before=old_build(OldParameters.from_dict(p.to_dict()))
            for role in carbon_roles(p):check(now[role].cut(before[role]).Volume<1e-6 and before[role].cut(now[role]).Volume<1e-6,shape+'/'+layout+': unchanged '+role)
            report['original_configurations']+=1
    doc=App.openDocument(str(Path(__file__).resolve().parents[1]/'examples/Example_FourLobe_MotorEnds.FCStd'))
    settings=doc.getObject('FrameParameters');p=read_parameters(settings);update_frame(settings,p)
    check(read_parameters(settings)==p,'Earlier native keeps dimensions')
    check(tuple(settings.getEnumerationsOfProperty('MotorPadShape'))==MOTOR_PAD_SHAPES,'Earlier native gains ten choices')
    App.closeDocument(doc.Name);report['status']='passed'
except Exception:report.update(status='failed',error=traceback.format_exc());print(report['error'],flush=True)
finally:
    for doc in list(App.listDocuments().values()):App.closeDocument(doc.Name)
    (output/'test_report.json').write_text(json.dumps(report,indent=2));print('MOTOR PADS',report['status'],len(report['checks']),flush=True)
