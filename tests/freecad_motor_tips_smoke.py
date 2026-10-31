"""FreeCAD: outward motor tips, relief web, manufacturing and native restore."""
from dataclasses import replace
from pathlib import Path
import json,math,os,sys,tempfile,traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from rotorforge import __version__
from freecad.rotorforge.parameters import Parameters,LAYOUTS,arm_layouts,plate_levels,load_parameters
from freecad.rotorforge.motor_pads import EXTENDED_MOTOR_PAD_SHAPES,MOTOR_PAD_SHAPES,motor_tip_slots
from freecad.rotorforge.geometry import build_shapes,carbon_roles,flat_plate_shape,capsule,cylinder
from freecad.rotorforge.document import create_frame,read_parameters,update_frame,component_objects
from freecad.rotorforge.exporters import export_package,profile_entities

output=Path(os.environ.get('ROTORFORGE_TEST_OUTPUT',tempfile.mkdtemp(prefix='rotorforge-motor-tips-')))
output.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[],'export_folders':[],'freecad_version':'.'.join(App.Version()[:3])}
def check(ok,message):
    if not ok:raise AssertionError(message)
    report['checks'].append(message)

try:
    configurations=[]
    for shape in EXTENDED_MOTOR_PAD_SHAPES:
        for layout in LAYOUTS:
            for design,position in (('3 plates','Below bottom plate'),('2 plates','Below bottom plate'),('2 plates','Above bottom plate')):
                p=Parameters(Layout=layout,Wheelbase=270,MotorPadShape=shape,PlateDesign=design,
                             TwoPlateArmPosition=position,ArmBracesEnabled=design=='2 plates',StandoffHeight=35)
                tag=shape+'/'+layout+'/'+design+'/'+position;shapes=build_shapes(p);z=plate_levels(p)['arm_z']
                configurations.append(p)
                for role in carbon_roles(p):check(shapes[role].isValid() and len(shapes[role].Solids)==1,tag+': connected '+role)
                for arm in arm_layouts(p):
                    role='Arm'+arm['name'];actual=shapes[role];ux,uy=arm['unit'];mx,my=arm['motor']
                    local=actual.copy();local.translate(App.Vector(-mx,-my,0));local.rotate(App.Vector(),App.Vector(0,0,1),-math.degrees(math.atan2(uy,ux)))
                    check(abs(local.BoundBox.XMax-(p.MotorPadDiameter/2+p.MotorTipLength))<1e-6,tag+': full outward reach '+role)
                    for pt in arm['motor_holes']:
                        bore=cylinder(*pt,p.MotorHoleDiameter/2-.02,z-.1,p.ArmThickness+.2)
                        check(actual.common(bore).Volume<1e-6,tag+': motor screw bore '+role)
                        support=cylinder(*pt,p.MotorHoleDiameter/2+p.MinimumWeb,z,p.ArmThickness).cut(cylinder(*pt,p.MotorHoleDiameter/2,z-.1,p.ArmThickness+.2))
                        check(abs(support.common(actual).Volume-support.Volume)<1e-5,tag+': complete bolt web '+role)
                    for a,b,radius in motor_tip_slots(p,arm):
                        tool=capsule(a,b,radius,z-.1,p.ArmThickness+.2)
                        check(actual.common(tool).Volume<1e-6,tag+': through-cut tip slot '+role)
                        centre=((a[0]+b[0])/2,(a[1]+b[1])/2)
                        check((centre[0]-mx)*ux+(centre[1]-my)*uy>p.MotorPadDiameter/2,tag+': slot faces outward '+role)
                        for sign in (-1,1):
                            offset=sign*(radius+p.MinimumWeb*.6)
                            check(actual.isInside(App.Vector(centre[0]-uy*offset,centre[1]+ux*offset,z+p.ArmThickness/2),1e-7,True),tag+': material beside tip slot '+role)
                if layout=='True X' and design=='3 plates':
                    uncut=build_shapes(replace(p,MotorTipSlotEnabled=False))
                    radius=p.MotorTipSlotWidth/2;expected=(p.MotorTipSlotWidth*(p.MotorTipSlotLength-p.MotorTipSlotWidth)+math.pi*radius**2)*p.ArmThickness
                    for arm in arm_layouts(p):
                        role='Arm'+arm['name'];check(abs(uncut[role].Volume-shapes[role].Volume-expected)<1e-5,tag+': exact slot volume '+role)
                    for role in ('BottomPlate','MidPlate','TopPlate'):
                        check(abs(uncut[role].Volume-shapes[role].Volume)<1e-7,tag+': slot toggle leaves '+role)
    for shape in EXTENDED_MOTOR_PAD_SHAPES:
        p=Parameters(MotorPadShape=shape,MotorPadDiameter=36,MotorSpacingX=16,MotorSpacingY=19)
        shapes=build_shapes(p);check(all(shapes[r].isValid() for r in carbon_roles(p)),shape+': rectangular motor pattern')
    for p in [q for q in configurations if q.Layout=='True X' and not (q.PlateDesign=='2 plates' and q.TwoPlateArmPosition=='Above bottom plate')]:
        tag=p.MotorPadShape+'/'+p.PlateDesign;settings=create_frame(p);doc=settings.Document
        folder=export_package(settings,output/'exports');report['export_folders'].append(str(folder))
        info=json.loads((folder/'ExportInfo.json').read_text())
        check(info['generator_version']==__version__,tag+': export version')
        check(info['motor_pad']['shape']==p.MotorPadShape,tag+': shape metadata')
        check(info['motor_pad']['tip_extension_mm']==p.MotorTipLength,tag+': tip extension metadata')
        check(len(info['motor_pad']['tip_slots_frame_mm'])==4,tag+': coordinates for all arm slots')
        assembly=Part.read(str(folder/'FrameAssembly.step'));check(assembly.isValid(),tag+': actual STEP reimport')
        for arm in arm_layouts(p):
            role='Arm'+arm['name'];entities=profile_entities(flat_plate_shape(component_objects(settings)[role].Shape,role))
            check(any(e[0]=='ARC' and abs(e[3]-p.MotorTipSlotWidth/2)<1e-6 for e in entities),tag+': analytic slot arcs '+role)
            check((folder/'CuttingProfiles'/(role+'.dxf')).stat().st_size>100,tag+': DXF '+role)
            check((folder/'CuttingProfiles'/(role+'.svg')).stat().st_size>100,tag+': SVG '+role)
        path=output/('Native_'+p.MotorPadShape.replace(' ','_')+'_'+p.PlateDesign[0]+'.FCStd')
        doc.saveAs(str(path));App.closeDocument(doc.Name);doc=App.openDocument(str(path));settings=doc.getObject('FrameParameters');doc.recompute();doc.UndoMode=1
        check(read_parameters(settings)==p,tag+': native controls persist')
        check(settings.Status.startswith('Valid'),tag+': valid native restore')
        update_frame(settings,replace(p,MotorTipSlotEnabled=False));doc.undo();doc.recompute()
        check(read_parameters(settings)==p,tag+': Undo restores the slot')
        App.closeDocument(doc.Name)
    old=Path(__file__).resolve().parents[1]/'examples/Example_FPV_Mini22_Vertical6p5.FCStd'
    doc=App.openDocument(str(old));settings=doc.getObject('FrameParameters');p=read_parameters(settings);update_frame(settings,p)
    check(set(settings.getEnumerationsOfProperty('MotorPadShape'))==set(MOTOR_PAD_SHAPES),'Earlier native example gains the new outline choices')
    check(settings.MotorTipLength.Value==8 and p.MotorPadShape=='Round','Earlier round model retains its dimensions')
    App.closeDocument(doc.Name)
    report['status']='passed'
except Exception:
    report['status']='failed';report['error']=traceback.format_exc();print(report['error'],flush=True)
finally:
    for doc in list(App.listDocuments().values()):App.closeDocument(doc.Name)
    (output/'test_report.json').write_text(json.dumps(report,indent=2))
    print('MOTOR TIPS',report['status'],len(report['checks']),flush=True)
