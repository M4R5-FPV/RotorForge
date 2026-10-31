"""FreeCADCmd: adjustable camera, independent decks, airflow and motor pads."""
from dataclasses import replace
from pathlib import Path
import json,math,os,sys,tempfile,traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
import Mesh
from freecad.rotorforge.parameters import (Parameters,arm_layouts,plate_levels,stack_reference_z,stack_mounting_role,
    bottom_bounds,mid_bounds,top_bounds,stack_holes)
from freecad.rotorforge.fpv import camera_mounts,camera_body_centre
from freecad.rotorforge.cutouts import encode_patterns,parse_patterns
from freecad.rotorforge.geometry import build_shapes,carbon_roles,physical_roles,flat_plate_shape,cylinder
from freecad.rotorforge.document import create_frame,update_frame,read_parameters,component_objects
from freecad.rotorforge.exporters import export_package,profile_entities
from freecad.rotorforge.motor_pads import MOTOR_PAD_SHAPES

output=Path(os.environ.get('ROTORFORGE_TEST_OUTPUT',tempfile.mkdtemp(prefix='rotorforge-design-options-')));output.mkdir(parents=True,exist_ok=True)
report={'status':'running','freecad_version':'.'.join(App.Version()[:3]),'checks':[],'export_folders':[]}
def check(ok,message):
    if not ok:raise AssertionError(message)
    report['checks'].append(message)
def rejects(p,message):
    try:build_shapes(p)
    except ValueError:check(True,message)
    else:raise AssertionError(message)

try:
    # Exact, independently supported rear mid. There is no bottom beneath VTX.
    base=Parameters(FPVEnabled=True,CameraSideBoltSpacing=8,CameraTiltMax=55,StandoffHeight=35,CameraTiltMechanism='Upper pivot + lower arc',
                    BottomReachMode='Custom',BottomRearReach=45,BottomFrontReach=87,
                    MidReachMode='Custom',MidRearReach=100,TopReachMode='Custom',TopRearReach=101,TopFrontReach=86)
    shapes=build_shapes(base)
    check(bottom_bounds(base)[0]==-45 and shapes['BottomPlate'].BoundBox.YMin>=-45-1e-7,'Matched bottom tabs stay within the custom rear limit')
    check(abs(shapes['MidPlate'].BoundBox.YMin+100)<1e-7,'Mid rear extends independently beyond bottom')
    check(abs(shapes['TopPlate'].BoundBox.YMin+101)<1e-7,'Top rear stays independently configured')
    check(not any(e[0]=='CIRCLE' and e[2]<-50 for e in profile_entities(shapes['BottomPlate'])),'No unsupported VTX bores in three-plate bottom')
    check(sum(e[0]=='CIRCLE' and e[2]<-50 for e in profile_entities(shapes['MidPlate']))==8,'Both VTX patterns remain in the independent mid')
    check(build_shapes(Parameters())['BottomPlate'].BoundBox.YMin>-45,'Automatic three-plate bottom ends at rear arm sandwich')
    # A true pivot and curved slot, with exact circle arcs in cutting exports.
    mount=camera_mounts(base)[0];x=sum(mount['plate_x'])/2;cy,cz=mount['side_holes'][0]
    for angle in (0,20,40,55):
        y,z=cy+8*math.sin(math.radians(angle)),cz-8*math.cos(math.radians(angle))
        probe=Part.makeCylinder(.95,base.CameraBracketThickness+2,App.Vector(mount['plate_x'][0]-1,y,z),App.Vector(1,0,0))
        check(probe.common(shapes['CameraMountLeft']).Volume<1e-7,f'{angle}°: lower camera screw travels freely in the arc slot')
    for angle in (-12,67):
        y,z=cy+8*math.sin(math.radians(angle)),cz-8*math.cos(math.radians(angle))
        check(shapes['CameraMountLeft'].isInside(App.Vector(x,y,z),1e-7,True),f'{angle}°: material remains beyond adjustment slot end stop')
    entities=profile_entities(flat_plate_shape(shapes['CameraMountLeft'],'CameraMountLeft'))
    check(any(e[0]=='ARC' and abs(e[3]-9.1)<1e-7 for e in entities),'Exact outer arc radius in camera profile')
    check(any(e[0]=='ARC' and abs(e[3]-6.9)<1e-7 for e in entities),'Exact inner arc radius in camera profile')
    for tilt in (5,40,55):
        q=replace(base,CameraTilt=tilt);s=build_shapes(q)
        for role in carbon_roles(base):
            check(abs(s[role].Volume-shapes[role].Volume)<1e-6 and s[role].common(shapes[role]).Volume>shapes[role].Volume-1e-5,
                  role+': preview angle leaves manufactured geometry unchanged')
    fixed=replace(base,CameraMountMode='Fixed',CameraTilt=25)
    sf=build_shapes(fixed);m=camera_mounts(fixed)[0]
    check(len(m['side_holes'])==2 and not m['side_arcs'],'Fixed tilt uses two physical screw holes per side')
    check(abs(math.dist(*m['side_holes'])-8)<1e-8,'Fixed screw pitch matches measured camera pitch')
    rejects(replace(fixed,CameraSideBoltSpacing=0),'Single screw cannot falsely claim a fixed angle')
    rejects(replace(base,CameraTilt=60),'Preview outside configured adjustment range rejected')
    rejects(replace(base,StandoffHeight=10),'Insufficient full-range camera clearance rejected')
    # Stack bottom is exactly carrier top; only the entered spacer offsets it.
    for mode,clamp,position in (('2 plates',False,'Below bottom plate'),('2 plates',True,'Below bottom plate'),
                                ('2 plates',True,'Above bottom plate'),('3 plates',False,'Above bottom plate')):
        p=Parameters(PlateDesign=mode,ArmBracesEnabled=clamp,TwoPlateArmPosition=position,StandoffHeight=35)
        s=build_shapes(p);carrier=stack_mounting_role(p)
        check(abs(s['StackEnvelope'].BoundBox.ZMin-s[carrier].BoundBox.ZMax)<1e-7,carrier+': zero spacer puts stack on supporting face')
        q=replace(p,StackMountHeight=4);t=build_shapes(q)
        check(abs(t['StackEnvelope'].BoundBox.ZMin-s[carrier].BoundBox.ZMax-4)<1e-7,carrier+': explicit spacer is the only lift')
    rejects(Parameters(PlateDesign='2 plates',TwoPlateArmPosition='Above bottom plate'),
            'Direct bottom stack/arm collision is reported instead of applying a hidden lift')
    p=Parameters(PlateDesign='2 plates',TwoPlateArmPosition='Above bottom plate',StackMountHeight=5.2)
    check(abs(build_shapes(p)['StackEnvelope'].BoundBox.ZMin-7.2)<1e-7,'Explicit arm clearance spacer remains exact')
    # Multiple independent patterns, every supported shape and camera sides.
    patterns=[dict(role='BottomPlate',shape='Circle',width=6,x=0,y=0),
              dict(role='MidPlate',shape='Rounded rectangle',width=8,length=14,x=0,y=-68),
              dict(role='TopPlate',shape='Hexagon',width=5,length=8,x=0,y=0,columns=2,rows=2,pitch_x=12,pitch_y=16,rotation=10),
              dict(role='CameraMountLeft',shape='Circle',width=2,x=-5,y=5),
              dict(role='CameraMountRight',shape='Slot',width=2,length=5,x=-5,y=8),
              dict(role='ArmKeystone',shape='Circle',width=4,x=0,y=0)]
    for arm in arm_layouts(base):
        patterns.append(dict(role='Arm'+arm['name'],shape='Slot',width=3,length=10,
                             x=(arm['root'][0]+arm['motor'][0])/2,y=(arm['root'][1]+arm['motor'][1])/2,
                             rotation=math.degrees(math.atan2(arm['unit'][1],arm['unit'][0]))-90))
    ventilated=replace(base,KeystoneEnabled=True,CutoutPatterns=encode_patterns(patterns))
    plain=replace(ventilated,CutoutPatterns='[]');sv=build_shapes(ventilated);sp=build_shapes(plain)
    for role in carbon_roles(ventilated):
        check(sv[role].isValid() and len(sv[role].Solids)==1,role+': airflow leaves one connected solid')
        check(sv[role].Volume<sp[role].Volume,role+': independent airflow removes material')
    check(abs(sp['BottomPlate'].Volume-sv['BottomPlate'].Volume-math.pi*9*base.BottomThickness)<1e-6,'Circle airflow removes exact analytical volume')
    check(abs(sp['CameraMountLeft'].Volume-sv['CameraMountLeft'].Volume-math.pi*base.CameraBracketThickness)<1e-6,'Camera airflow uses its own Y/Z coordinates')
    for pattern in (dict(role='TopPlate',shape='Circle',width=8,x=24,y=0),
                    dict(role='MidPlate',shape='Circle',width=4,x=15.25,y=15.25),
                    dict(role='TopPlate',shape='Circle',width=4,x=0,y=0,columns=2,pitch_x=4),
                    dict(role='CameraMountLeft',shape='Circle',width=3,x=-6,y=0),
                    dict(role='CameraMountLeft',shape='Circle',width=4,x=0,y=cz-base.BottomThickness)):
        rejects(replace(base,CutoutPatterns=encode_patterns([pattern])),'Unsafe airflow at '+pattern['role']+' rejected')
    disabled=replace(base,CutoutPatterns=encode_patterns([dict(role='TopPlate',shape='Circle',width=100,enabled=False)]))
    check(abs(build_shapes(disabled)['TopPlate'].Volume-shapes['TopPlate'].Volume)<1e-6,'Disabled patterns retain settings without cutting')
    # Every profile preserves the exact motor bores and root positions.
    volumes=[]
    for shape in MOTOR_PAD_SHAPES:
        p=Parameters(MotorPadShape=shape,MotorHoleRotation=45,MotorBoltCircle=22.627416997969522);s=build_shapes(p);arm=arm_layouts(p)[0];actual=s['ArmFrontRight']
        volumes.append(round(actual.Volume,4))
        for pt in arm['motor_holes']:
            probe=cylinder(*pt,p.MotorHoleDiameter/2-.05,plate_levels(p)['arm_z']-1,p.ArmThickness+2)
            check(actual.common(probe).Volume<1e-7,shape+': actual motor bore stays at configured point')
        check(actual.isValid() and len(actual.Solids)==1,shape+': motor end connects to arm')
    check(len(set(volumes))==len(MOTOR_PAD_SHAPES),'Every motor end choice produces a distinct manufactured profile')
    # Native persistence, Undo, mass and complete manufacturing packages.
    doc=App.newDocument('RotorForgeDesign09');doc.UndoMode=1;settings=create_frame(ventilated,doc)
    check(settings.getTypeIdOfProperty('CutoutPatterns')=='App::PropertyString','Native airflow JSON property exists')
    check(abs(settings.CarbonMassGrams-sum(sv[r].Volume for r in carbon_roles(ventilated))*base.CarbonDensity/1000)<1e-6,'Carbon mass uses ventilated solids')
    variants=[ventilated,replace(fixed,MotorPadShape='Rounded square'),
              Parameters(FPVEnabled=True,PlateDesign='2 plates',ArmBracesEnabled=True,StandoffHeight=35,
                         MotorPadShape='Chamfered square',CutoutPatterns=encode_patterns([dict(role='ArmClampPlate',shape='Slot',width=6,length=14)])),
              Parameters(PlateDesign='2 plates',MotorPadShape='Four-lobe')]
    for index,p in enumerate(variants):
        update_frame(settings,p);folder=export_package(settings,output);report['export_folders'].append(str(folder))
        info=json.loads((folder/'ExportInfo.json').read_text())
        check(info['airflow_patterns']==parse_patterns(p.CutoutPatterns),'Export records exact independent airflow patterns')
        check(info['motor_pad']['shape']==p.MotorPadShape,'Export records motor end choice')
        step=Part.read(str(folder/'FrameAssembly.step'))
        check(step.isValid() and len(step.Solids)==len(carbon_roles(p))+4,'Assembly STEP contains every active ventilated component')
        if p.FPVEnabled:
            for role in ('CameraMountLeft','CameraMountRight'):
                mesh=Mesh.Mesh(str(folder/'CameraPlates'/(role+'.stl')))
                check(mesh.isSolid() and abs(mesh.BoundBox.ZMin)<1e-6,'Ventilated camera STL is closed and flat at Z=0')
        path=output/f'Design09_{index}.FCStd';doc.saveAs(str(path));name=settings.Name;App.closeDocument(doc.Name)
        doc=App.openDocument(str(path));settings=doc.getObject(name);doc.recompute();doc.UndoMode=1
        check(read_parameters(settings)==p,'All new choices persist through native save/reopen')
    before=read_parameters(settings);update_frame(settings,replace(before,MotorPadShape='Round'));doc.undo();doc.recompute()
    check(read_parameters(settings)==before,'Undo restores selected motor pad')
    report['status']='passed'
except Exception:
    report['status']='failed';report['error']=traceback.format_exc()
finally:
    for doc in list(App.listDocuments().values()):App.closeDocument(doc.Name)
    (output/'test_report.json').write_text(json.dumps(report,indent=2))
    print('ROTORFORGE DESIGN OPTIONS',report['status'],len(report['checks']),str(output),flush=True)
