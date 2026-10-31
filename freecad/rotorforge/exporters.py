"""STEP assembly plus exact, dependency-free line/arc/circle cutting files."""
import csv
from datetime import datetime
import html
import json
import math
from pathlib import Path
import shutil

import FreeCAD as App
import Part

from . import __version__
from .parameters import (require_valid, save_parameters, prop_gap, three_plate, standoff_layouts, standoff_pair_count,
                         arm_clamp_grip, arm_brace_layouts, arm_braces, top_bounds,
                         stack_mounting_role, bottom_stack_hole_diameter, plate_levels, stack_holes, strap_slots, stack_reference_z)
from .geometry import carbon_roles, physical_roles, build_shapes, flat_plate_shape
from .document import read_parameters
from .fpv import CAMERA_ROLES, camera_mounts, camera_slots, camera_pivot_height, vtx_holes, camera_position_y, camera_base_extensions
from .parameters import upper_clamp_active, underside_clamp_active, underside_clamp_layout
from .cutouts import parse_patterns
from .parameters import bottom_bounds, bottom_body_bounds, bottom_tabs, mid_bounds, keystone_active, keystone_retainers
from .plate_profiles import CENTRE_WIDTH_FIELDS
from .parameters import motor_hole_offsets
from .motor_pads import extended_motor_pad, motor_tip_slots
from .parameters import arm_layouts, frame_bolt_offsets, motor_centres
from .arm_roots import fitted_roots, root_joint_planes, compact_key_outline, compact_key_centre, root_width, widened_roots


def profile_entities(shape, offset=(0.0, 0.0), curve_tolerance=None):
    """Extract top-face curves; optionally approximate other curves for soft pads."""
    faces = [face for face in shape.Faces if abs(face.normalAt(0, 0).z) > 0.999999]
    if not faces:
        raise ValueError("No horizontal cutting face found.")
    face = max(faces, key=lambda item: item.CenterOfMass.z)
    entities = []
    ox, oy = offset
    for wire in face.Wires:
        for edge in wire.Edges:
            curve = edge.Curve
            if isinstance(curve, Part.Circle):
                c, radius = curve.Center, curve.Radius
                if edge.isClosed():
                    entities.append(("CIRCLE", c.x + ox, c.y + oy, radius))
                else:
                    first, last = edge.valueAt(edge.FirstParameter), edge.valueAt(edge.LastParameter)
                    middle = edge.valueAt((edge.FirstParameter + edge.LastParameter) / 2)
                    start = math.degrees(math.atan2(first.y - c.y, first.x - c.x)) % 360
                    end = math.degrees(math.atan2(last.y - c.y, last.x - c.x)) % 360
                    mid = math.degrees(math.atan2(middle.y - c.y, middle.x - c.x)) % 360
                    # DXF ARC is counterclockwise, independent of edge orientation.
                    if (mid - start) % 360 > (end - start) % 360 + 1e-7:
                        start, end = end, start
                    entities.append(("ARC", c.x + ox, c.y + oy, radius, start, end))
            elif isinstance(curve,Part.Ellipse):
                c=curve.Center;a,b=curve.MajorRadius,curve.MinorRadius;u=curve.XAxis
                def angle(point):
                    dx,dy=point.x-c.x,point.y-c.y
                    return math.atan2((-u.y*dx+u.x*dy)/b,(u.x*dx+u.y*dy)/a)%(2*math.pi)
                if edge.isClosed():start,end=0.,2*math.pi
                else:
                    start=angle(edge.valueAt(edge.FirstParameter));end=angle(edge.valueAt(edge.LastParameter))
                    mid=angle(edge.valueAt((edge.FirstParameter+edge.LastParameter)/2))
                    if (mid-start)%(2*math.pi)>(end-start)%(2*math.pi)+1e-7:start,end=end,start
                entities.append(('ELLIPSE',c.x+ox,c.y+oy,u.x*a,u.y*a,b/a,start,end))
            elif curve.__class__.__name__ in ("Line", "LineSegment"):
                a, b = edge.valueAt(edge.FirstParameter), edge.valueAt(edge.LastParameter)
                entities.append(("LINE", a.x + ox, a.y + oy, b.x + ox, b.y + oy))
            elif curve.__class__.__name__=='BezierCurve' and len(curve.getPoles()) in (3,4):
                from .bezier import trim_cubic
                points=trim_cubic(tuple((v.x,v.y) for v in curve.getPoles()),edge.FirstParameter,edge.LastParameter)
                entities.append(('SPLINE',*(value for x,y in points for value in (x+ox,y+oy))))
            elif curve_tolerance is not None:
                points=edge.discretize(Deflection=curve_tolerance)
                entities.extend(('LINE',a.x+ox,a.y+oy,b.x+ox,b.y+oy) for a,b in zip(points,points[1:]))
            else:
                raise ValueError("Unsupported cutting curve: " + curve.__class__.__name__)
    return entities


def write_dxf(path, profiles):
    """DXF R2000, millimetres, separate layer per component. No tessellation."""
    data = []
    handle = 0x100
    def pair(code, value):
        data.extend((str(code), f"{value:.10f}" if isinstance(value, float) else str(value)))
    def new_handle():
        nonlocal handle
        pair(5, format(handle, "X"))
        handle += 1
    pair(0, "SECTION"); pair(2, "HEADER")
    pair(9, "$ACADVER"); pair(1, "AC1015")
    pair(9, "$INSUNITS"); pair(70, 4)
    pair(9, "$MEASUREMENT"); pair(70, 1)
    pair(9, "$HANDSEED"); pair(5, "FFFF")
    pair(0, "ENDSEC")
    pair(0, "SECTION"); pair(2, "TABLES")
    pair(0, "TABLE"); pair(2, "LTYPE"); new_handle(); pair(100, "AcDbSymbolTable"); pair(70, 1)
    pair(0, "LTYPE"); new_handle(); pair(100, "AcDbSymbolTableRecord"); pair(100, "AcDbLinetypeTableRecord")
    pair(2, "CONTINUOUS"); pair(70, 0); pair(3, "Solid line"); pair(72, 65); pair(73, 0); pair(40, 0.0)
    pair(0, "ENDTAB")
    pair(0, "TABLE"); pair(2, "LAYER"); new_handle(); pair(100, "AcDbSymbolTable"); pair(70, len(profiles) + 1)
    for name in ["0"] + [name for name, entities in profiles]:
        pair(0, "LAYER"); new_handle(); pair(100, "AcDbSymbolTableRecord"); pair(100, "AcDbLayerTableRecord")
        pair(2, name); pair(70, 0); pair(62, 7); pair(6, "CONTINUOUS")
    pair(0, "ENDTAB"); pair(0, "ENDSEC")
    pair(0, "SECTION"); pair(2, "ENTITIES")
    for name, entities in profiles:
        for item in entities:
            kind, *coords = item
            pair(0, kind); new_handle(); pair(100, "AcDbEntity"); pair(8, name)
            if kind == "LINE":
                pair(100, "AcDbLine")
                pair(10, coords[0]); pair(20, coords[1]); pair(30, 0.0)
                pair(11, coords[2]); pair(21, coords[3]); pair(31, 0.0)
            elif kind == 'SPLINE':
                pair(100,'AcDbSpline');pair(70,8);pair(71,3);pair(72,8);pair(73,4);pair(74,0)
                pair(210,0.);pair(220,0.);pair(230,1.)
                for knot in (0.,0.,0.,0.,1.,1.,1.,1.):pair(40,knot)
                for i in range(0,8,2):pair(10,coords[i]);pair(20,coords[i+1]);pair(30,0.)
            elif kind == 'ELLIPSE':
                pair(100,'AcDbEllipse')
                pair(10,coords[0]);pair(20,coords[1]);pair(30,0.)
                pair(11,coords[2]);pair(21,coords[3]);pair(31,0.)
                pair(40,coords[4]);pair(41,coords[5]);pair(42,coords[6])
            else:
                pair(100, "AcDbCircle")
                pair(10, coords[0]); pair(20, coords[1]); pair(30, 0.0); pair(40, coords[2])
                if kind == "ARC":
                    pair(100, "AcDbArc")
                    pair(50, coords[3]); pair(51, coords[4])
    pair(0, "ENDSEC"); pair(0, "EOF")
    Path(path).write_text("\n".join(data) + "\n", encoding="ascii")


def write_svg(path, profiles, width, height, labels=(), margin=5.0):
    """1 SVG user unit = 1 mm. Cutting geometry contains only exact primitives."""
    w, h = width + 2 * margin, height + 2 * margin
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.6f}mm" height="{h:.6f}mm" viewBox="0 0 {w:.6f} {h:.6f}">',
           '<title>RotorForge cutting profiles — millimetres</title>',
           f'<g transform="translate({margin},{h - margin}) scale(1,-1)" fill="none" stroke="#111111" stroke-width="0.15">']
    for name, entities in profiles:
        svg.append(f'<g id="{html.escape(name)}">')
        for kind, *v in entities:
            if kind == "LINE":
                svg.append(f'<line x1="{v[0]:.9f}" y1="{v[1]:.9f}" x2="{v[2]:.9f}" y2="{v[3]:.9f}"/>')
            elif kind == "CIRCLE":
                svg.append(f'<circle cx="{v[0]:.9f}" cy="{v[1]:.9f}" r="{v[2]:.9f}"/>')
            elif kind == 'SPLINE':
                svg.append(f'<path d="M {v[0]:.9f},{v[1]:.9f} C {v[2]:.9f},{v[3]:.9f} {v[4]:.9f},{v[5]:.9f} {v[6]:.9f},{v[7]:.9f}"/>')
            elif kind == 'ELLIPSE':
                cx,cy,mx,my,ratio,start,end=v;a=math.hypot(mx,my);b=a*ratio
                rotation=math.degrees(math.atan2(my,mx))
                if abs(end-start-2*math.pi)<1e-7:
                    svg.append(f'<ellipse cx="{cx:.9f}" cy="{cy:.9f}" rx="{a:.9f}" ry="{b:.9f}" transform="rotate({rotation:.9f},{cx:.9f},{cy:.9f})"/>')
                else:
                    def point(t):return (cx+mx*math.cos(t)-my*ratio*math.sin(t),cy+my*math.cos(t)+mx*ratio*math.sin(t))
                    x1,y1=point(start);x2,y2=point(end);large=1 if (end-start)%(2*math.pi)>math.pi else 0
                    svg.append(f'<path d="M {x1:.9f},{y1:.9f} A {a:.9f},{b:.9f} {rotation:.9f} {large},1 {x2:.9f},{y2:.9f}"/>')
            else:
                cx, cy, r, start, end = v
                a, b = math.radians(start), math.radians(end)
                large = 1 if (end - start) % 360 > 180 else 0
                svg.append(f'<path d="M {cx+r*math.cos(a):.9f},{cy+r*math.sin(a):.9f} '
                           f'A {r:.9f},{r:.9f} 0 {large},1 {cx+r*math.cos(b):.9f},{cy+r*math.sin(b):.9f}"/>')
        svg.append('</g>')
    svg.append('</g>')
    for text, x, y in labels:
        svg.append(f'<text x="{x+margin:.4f}" y="{h-margin-y:.4f}" font-family="sans-serif" font-size="3">{html.escape(text)}</text>')
    svg.append('</svg>')
    Path(path).write_text("\n".join(svg) + "\n", encoding="utf-8")


def cutting_profiles(shapes, folder, roles, p=None):
    """Write individual and thickness-grouped profiles from one shared layout."""
    from .cutting_layout import arrange_profiles,ARM_ROLES
    folder=Path(folder);folder.mkdir()
    items=[];flats={};faces={}
    arms={'Arm'+a['name']:a for a in arm_layouts(p)} if p is not None else {}
    for role in roles:
        shape=flat_plate_shape(shapes[role],role,p).copy();angle=0.
        if role in ARM_ROLES:
            if role not in arms:raise ValueError('Frame parameters are required to orient arm cutting profiles.')
            ux,uy=arms[role]['unit'];up=ARM_ROLES.index(role)%2==0
            angle=(90. if up else -90.)-math.degrees(math.atan2(uy,ux))
            shape.rotate(App.Vector(),App.Vector(0,0,1),angle)
        box=shape.BoundBox
        items.append(dict(role=role,width=box.XLength,height=box.YLength,thickness=box.ZLength,
                          rotation_deg=angle,motor_end=('top' if ARM_ROLES.index(role)%2==0 else 'bottom') if role in ARM_ROLES else None))
        flats[role]=shape
        face=max((f for f in shape.Faces if abs(f.normalAt(0,0).z)>.999999),key=lambda f:f.CenterOfMass.z).copy()
        face.translate(App.Vector(-box.XMin,-box.YMin,-face.CenterOfMass.z));faces[role]=face
        entities=profile_entities(shape,(-box.XMin,-box.YMin))
        write_dxf(folder/(role+'.dxf'),[(role,entities)])
        write_svg(folder/(role+'.svg'),[(role,entities)],box.XLength,box.YLength,margin=0.)
    layout=arrange_profiles(items);combined=[]
    for sheet in layout['sheets']:
        local=[]
        for item in sheet['parts']:
            role=item['role'];shape=flats[role];b=shape.BoundBox
            local.append((role,profile_entities(shape,(item['x']-b.XMin,item['y']-b.YMin))))
            combined.append((role,profile_entities(shape,(item['x']-b.XMin,item['y']+sheet['combined_y']-b.YMin))))
        write_dxf(folder/('Stock_'+sheet['token']+'.dxf'),local)
        write_svg(folder/('Stock_'+sheet['token']+'.svg'),local,sheet['width'],sheet['height'],margin=0.)
    write_dxf(folder/'AllCarbonParts.dxf',combined)
    width=max(s['width'] for s in layout['sheets']);height=max(s['combined_y']+s['height'] for s in layout['sheets'])
    write_svg(folder/'AllCarbonParts.svg',combined,width,height,margin=0.)
    (folder/'Layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
    return layout,faces


def export_package(settings, destination):
    """Create a new subfolder each time. Existing exports are never overwritten."""
    p = read_parameters(settings)
    warnings = require_valid(p)
    shapes = build_shapes(p)
    active_carbon = carbon_roles(p)
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = root / ("RotorForge_" + stamp)
    index = 2
    while folder.exists():
        folder = root / ("RotorForge_" + stamp + "_" + str(index))
        index += 1
    folder.mkdir()
    try:
        Part.makeCompound([shapes[role] for role in physical_roles(p)]).exportStep(str(folder / "FrameAssembly.step"))
        layout,profile_faces=cutting_profiles(shapes, folder / "CuttingProfiles", active_carbon,p)
        machining=[]
        if keystone_retainers(p):
            box=flat_plate_shape(shapes['ArmClampPlate'],'ArmClampPlate',p).BoundBox
            for item in keystone_retainers(p):
                x,y=item['point']
                machining.append(dict(part='ArmClampPlate',operation='Countersink',face='Upper',
                                      x_frame_mm=x,y_frame_mm=y,x_dxf_mm=x-box.XMin,y_dxf_mm=y-box.YMin,
                                      through_diameter_mm=item['bore'],outer_diameter_mm=item['head_diameter'],
                                      included_angle_deg=90,depth_mm=item['countersink_depth']))
        from .nut_geometry import operations
        for op in operations(p):
            box=flat_plate_shape(shapes[op['part']],op['part'],p).BoundBox
            op.update(x_dxf_mm=op['x_frame_mm']-box.XMin,y_dxf_mm=op['y_frame_mm']-box.YMin);machining.append(op)
        if machining:
            columns=list(dict.fromkeys(k for row in machining for k in row))
            with (folder/'MachiningOps.csv').open('w',newline='',encoding='utf-8') as stream:
                writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(machining)
        if p.FPVEnabled:
            import MeshPart
            brackets=folder/'CameraPlates'
            brackets.mkdir()
            for role in CAMERA_ROLES:
                shapes[role].exportStep(str(brackets/(role+'.step')))
                printable=flat_plate_shape(shapes[role],role)
                box=printable.BoundBox
                printable.translate(App.Vector(-box.XMin,-box.YMin,-box.ZMin))
                mesh=MeshPart.meshFromShape(Shape=printable,LinearDeflection=.05,AngularDeflection=.15,Relative=False)
                mesh.write(str(brackets/(role+'.stl')))
        if p.LiPoPadEnabled:
            import MeshPart
            from .battery import printable_pad,make_pad,mounting_role
            pad_folder=folder/'LiPoPad';pad_folder.mkdir()
            shapes['LiPoPad'].exportStep(str(pad_folder/'LiPoPad_assembled.step'))
            printable=printable_pad(p,shapes['LiPoPad'])
            printable.exportStep(str(pad_folder/'LiPoPad_flat.step'))
            MeshPart.meshFromShape(Shape=printable,LinearDeflection=.05,AngularDeflection=.15,Relative=False).write(str(pad_folder/'LiPoPad.stl'))
            blank=printable_pad(p,make_pad(p,shapes[mounting_role(p)],grooves=False))
            b=blank.BoundBox;entities=profile_entities(blank,curve_tolerance=.01)
            write_dxf(pad_folder/'LiPoPad_outline.dxf',[('LiPoPad',entities)])
            write_svg(pad_folder/'LiPoPad_outline.svg',[('LiPoPad',entities)],b.XLength,b.YLength,margin=0.)
        from .flex import flex_roles
        from .flex_geometry import printable_flex
        if flex_roles(p):
            import MeshPart
            soft_folder=folder/'FlexibleParts';soft_folder.mkdir()
            for role in flex_roles(p):
                shapes[role].exportStep(str(soft_folder/(role+'_assembled.step')))
                printable=printable_flex(shapes[role],role)
                printable.exportStep(str(soft_folder/(role+'_print.step')))
                mesh=MeshPart.meshFromShape(Shape=printable,LinearDeflection=.08,AngularDeflection=.2,Relative=False)
                if role.startswith('ElectronicsGuard'):
                    from .mesh_cleanup import weld_micro_seams
                    mesh=weld_micro_seams(mesh)
                mesh.write(str(soft_folder/(role+'.stl')))
            (soft_folder/'PRINT_NOTES.txt').write_text('Dimensions are millimetres. Each file is a separate printable part. Test fit flexible material and compress camera pads only by the configured preload. Captured inserts retain the existing camera tilt paths. Check connector retention, screw length, wiring, props and real hardware. Printed flexibility and vibration performance are not simulated.\n')
        from .mass_properties import mass_properties
        metrics=mass_properties(p,shapes)
        (folder/'MassProperties.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8')
        save_parameters(folder / "FrameParameters.json", p)
        carbon_mass = sum(shapes[role].Volume for role in active_carbon) * p.CarbonDensity / 1000
        with (folder / "PartsList.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("Part", "Quantity", "Material", "Thickness_mm", "Estimated_mass_g"))
            for role in active_carbon:
                shape = shapes[role]
                thickness=p.CameraBracketThickness if role in CAMERA_ROLES else shape.BoundBox.ZLength
                writer.writerow((role, 1, "Carbon laminate", f"{thickness:.3f}", f"{shape.Volume*p.CarbonDensity/1000:.3f}"))
            if p.LiPoPadEnabled:
                writer.writerow(('LiPoPad',1,'User pad material',f'{p.LiPoPadThickness:.3f}',f"{metrics['pad_mass_g']:.3f}"))
            for role in flex_roles(p):writer.writerow((role,1,"Printed flexible material","",f"{shapes[role].Volume*p.FlexDensity/1000:.3f}"))
            groups = {}
            for stand in standoff_layouts(p):
                key = (stand["position"], stand["length"])
                groups[key] = groups.get(key, 0) + 1
            for (position, length), quantity in sorted(groups.items()):
                unit_mass=math.pi*(p.StandoffDiameter**2-p.StandoffHoleDiameter**2)/4*length*p.StandoffDensity/1000
                writer.writerow((position + " standoffs", quantity, "Modelled standoff material", f"{length:.3f}", f"{unit_mass:.3f}"))
            shared=[s for s in standoff_layouts(p) if s['shared_arm']]
            if len(shared)<8:
                writer.writerow(("Arm root bolts", 8-len(shared), "Hardware — grip below; add nut/thread engagement", f'{arm_clamp_grip(p):.3f}', ""))
            if shared:
                writer.writerow(('Arm clamp bolts into standoffs',len(shared),'Hardware — grip below; add thread engagement',f'{shared[0]["grip_length"]:.3f}',''))
            writer.writerow(('Standoff top screws',len(standoff_layouts(p)),'Hardware — top thickness plus thread engagement','',''))
            if len(shared)<len(standoff_layouts(p)):
                writer.writerow(('Standoff base screws',len(standoff_layouts(p))-len(shared),'Hardware — mounting plate plus thread engagement','',''))
            writer.writerow(("Motor bolts", 4*len(motor_hole_offsets(p)), "Hardware — match motor thread depth", "", ""))
            carrier=stack_mounting_role(p)
            writer.writerow(('FC stack mounting bolts',4,'Hardware — carrier thickness below; add spacer/stack/thread engagement',
                             f'{shapes[carrier].BoundBox.ZLength:.3f}',''))
            spacer_height=stack_reference_z(p)-plate_levels(p)['stack_deck_z']
            if spacer_height:
                writer.writerow(('FC stack spacers',4,'Hardware',f'{spacer_height:.3f}',''))
            if keystone_retainers(p):
                grip=p.BottomThickness+p.ArmThickness+p.ArmBraceThickness
                writer.writerow(('Keystone retaining countersunk bolts',2,'Hardware — 90 degree flush heads; material stack below; CSK length includes head; add nut/thread engagement',f'{grip:.3f}',''))
                writer.writerow(('Keystone retaining nuts',2,'Hardware — match retainer bolt threads; below key','',''))
            if p.FPVEnabled:
                writer.writerow(('Camera side screws',4 if p.CameraSideBoltSpacing else 2,'Hardware — match camera threads; verify engagement','',''))
                writer.writerow(('VTX mounting bolts',4,'Hardware — use one selected four-hole pattern','',''))
        if p.EstimateComponents:
            with (folder/'EquipmentMass.csv').open('w',newline='',encoding='utf-8') as stream:
                writer=csv.writer(stream);writer.writerow(('Part','Mass_g','CG_X_mm','CG_Y_mm','CG_Z_mm'))
                for item in metrics['equipment_items']:writer.writerow((item['part'],item['mass_g'],*item['centre_mm']))
        (folder / "ExportInfo.json").write_text(json.dumps({
            "generator_version": __version__, "freecad_version": App.Version()[:3],
            "mass_properties":metrics,
            "battery_reference":{"capacity_mah":1300,"nominal_cells":6,"dimensions_mm":[p.BatteryLength,p.BatteryWidth,p.BatteryHeight],"mass_g":p.BatteryMass,"mount":p.BatteryMount,"position_xy_mm":[p.BatteryX,p.BatteryY],"rotation_deg":p.BatteryRotation,"enabled":p.BatteryReferenceEnabled},
            "units": "mm", "carbon_mass_g": round(carbon_mass, 3),
            "minimum_prop_gap_mm": round(prop_gap(p), 3), "warnings": warnings,
            "plate_design": p.PlateDesign, "standoff_count": 2 * standoff_pair_count(p),
            "standoff_pair_count": standoff_pair_count(p), "standoffs": standoff_layouts(p),
            "cutting_files_include": list(active_carbon), "cutting_layout":layout, "reference_envelopes_excluded": True,
            "front_axis": "+Y", "initial_view": "Front isometric (+X, +Y, +Z)",
            'motor_layout':{'base_diagonal_mm':p.Wheelbase,
                            'actual_diagonal_mm':math.dist(motor_centres(p)[0],motor_centres(p)[2]),
                            'rear_arm_extension_mm':p.RearArmExtension if p.Layout=='Deadcat' else 0.,
                            'motor_centres_frame_mm':dict(zip(('FrontRight','FrontLeft','RearLeft','RearRight'),motor_centres(p)))},
            'arm_mounting':{'position':'Between bottom and mid' if three_plate(p) else p.TwoPlateArmPosition,
                            'clamp_grip_mm':arm_clamp_grip(p),'connecting_plates':arm_brace_layouts(p),
                            'lower_capture_plate':underside_clamp_layout(p),'arm_root_stack_reliefs_enabled':p.ArmRootReliefsEnabled,
                            'arm_root_stack_relief_shape':p.ArmRootReliefShape,
                            'root_fit':p.ArmRootFit,'joint_clearance_mm':p.ArmJointClearance if fitted_roots(p) else None,
                            'root_profile':{'width_mm':root_width(p),'beam_width_mm':p.ArmWidth,
                                            'wide_length_mm':p.ArmRootLength if widened_roots(p) else 0,
                                            'taper_length_mm':p.ArmRootTaperLength if widened_roots(p) else 0},
                            'bolt_layout':p.RootBoltLayout,
                            'bolt_coordinates':{'axes':'Frame X: right; frame Y: front; offsets from front-right root, reflected on left/rear arms',
                                                'reference_arm':'FrontRight',
                                                'reference_offsets_xy_mm':frame_bolt_offsets(p),
                                                'frame_mm':{a['name']:a['bolts'] for a in arm_layouts(p)},
                                                'shared_mount_ids':{'inner':'Bolt 1','outer':'Bolt 2'}},
                            'root_joint_planes':{a['name']:root_joint_planes(p,a,arm_layouts(p)) for a in arm_layouts(p)} if fitted_roots(p) else {},
                            'keystone':({'thickness_mm':p.ArmThickness,'edge_clearance_mm':p.KeystoneClearance,
                                         'profile':('Compact diamond' if p.KeystoneShape=='Diamond' else p.KeystoneShape) if fitted_roots(p) else 'Automatic arm seats',
                                         'outline_frame_mm':compact_key_outline(p,arm_layouts(p)) if fitted_roots(p) else None,
                                         'centre_frame_mm':compact_key_centre(arm_layouts(p)) if fitted_roots(p) else (0,0),
                                         'located_by':'Four arm seats',
                                         'stack_access_reliefs_mm':p.StackAccessDiameter,
                                         'retention':('Bottom / mid capture' if three_plate(p) else 'Bottom / lower capture plate' if underside_clamp_active(p) else 'Bottom / upper clamp capture'),
                                         'retainers':keystone_retainers(p)}
                                        if keystone_active(p) else None)},
            'nut_retention':{'arms':p.ArmNutMount,'stack_press_nuts':p.StackPressNuts,'press_nut_material_margin_mm':1.,'vtx_nuts':False},
            'stack':{'mounting_plate':stack_mounting_role(p),'deck_z_mm':plate_levels(p)['stack_deck_z'],
                     'hole_centres':stack_holes(p),'mounting_hole_diameter_mm':p.StackHoleDiameter,
                     'carrier_bore_diameter_mm':p.PressNutBore if p.StackPressNuts else p.StackHoleDiameter,
                     'reference_base_z_mm':stack_reference_z(p),'upper_nut_z_mm':stack_reference_z(p)+p.StackHeight,
                     'bottom_hole_diameter_mm':bottom_stack_hole_diameter(p),
                     'spacer_height_mm':stack_reference_z(p)-plate_levels(p)['stack_deck_z'],
                     'press_nuts':p.StackPressNuts,'press_nut_clearance_mm':0. if p.StackPressNuts else None,'configured_spacer_height_mm':p.StackMountHeight,'envelope_height_mm':p.StackHeight},
            'strap_slots_enabled':p.StrapSlotsEnabled,'strap_opening_style':p.StrapOpeningStyle,'strap_notch_depth':p.StrapNotchDepth,'strap_count':p.StrapCount,'strap_single_y':p.StrapSingleY,'strap_slots':strap_slots(p),
            'plate_bounds_mm':{'BottomPlate':bottom_bounds(p),'MidPlate':mid_bounds(p) if three_plate(p) else None,'TopPlate':top_bounds(p)},
            'bottom_rear_tabs':{'profile':'Clipped to rear arm roots' if three_plate(p) else 'Full two-plate bottom',
                               'body_bounds_mm':bottom_body_bounds(p),'bolt_envelopes_frame_mm':bottom_tabs(p),
                               'body_rear_datum':'FC stack centre' if three_plate(p) else None,
                               'body_rear_reach_mm':p.BottomBodyRearReach if three_plate(p) else None},
            'mid_front_tabs':({'profile':'Clipped to front arm roots',
                               'follows':['Root width and taper','Bolt positions','Fitted joints and key pockets','Bottom support outline']}
                              if three_plate(p) else None),
            'centre_sections':{'widths_mm':{role:getattr(p,field) for role,field in CENTRE_WIDTH_FIELDS.items()},
                               'full_width_length_mm':p.CentreSectionLength,'shoulder_length_mm':p.CentreShoulderLength,
                               'centre_y_mm':p.CentreSectionY,'arm_roots_follow_bottom':p.ArmRootsFollowCentre},
            'secondary_machining':machining,
            'airflow_patterns':parse_patterns(p.CutoutPatterns),
            'airflow_coordinates':{'horizontal_parts':'U = frame X; V = frame Y',
                                   'camera_parts':'U = Y offset from nominal camera centre; V = Z above bottom plate upper face',
                                   'grid':'Centred at U/V; rotation turns both cutouts and grid'},
            'motor_pad':{'hole_layout':p.MotorHoleLayout,'bolt_circle_mm':p.MotorBoltCircle,'hole_rotation_deg':p.MotorHoleRotation,'hole_offsets_mm':motor_hole_offsets(p),
                         'reference_diameter_mm':p.MotorReferenceDiameter,'reference_height_mm':p.MotorReferenceHeight,'prop_reference_height_mm':p.PropReferenceHeight,
                         'shape':p.MotorPadShape,'rotation_deg':p.MotorPadRotation,
                         'rotation_pivot':p.MotorPadRotationPivot,
                         'pivot_centres_frame_mm':{a['name']:a['pad_pivot'] for a in arm_layouts(p)},
                         'rotation_by_arm_deg':{a['name']:a['pad_rotation_deg'] for a in arm_layouts(p)},
                         'hole_centres_frame_mm':{a['name']:a['motor_holes'] for a in arm_layouts(p)},'width_mm':p.MotorPadDiameter,'corner_radius_or_chamfer_mm':p.MotorPadCornerRadius,
                         'tip_extension_mm':p.MotorTipLength if extended_motor_pad(p) else 0,
                         'tip_slots_local_mm':motor_tip_slots(p),
                         'tip_slots_frame_mm':{a['name']:motor_tip_slots(p,a) for a in arm_layouts(p)}},
            "fpv_enabled":p.FPVEnabled,
            "fpv": ({'video_system':p.VideoSystem,'camera_width_mm':p.CameraWidth,
                     'camera_tilt_deg':p.CameraTilt,'camera_side_plates':camera_mounts(p),
                     'camera_mount_mode':p.CameraMountMode,
                     'camera_adjustable_range_deg':[p.CameraTiltMin,p.CameraTiltMax] if p.CameraMountMode=='Variable' else None,
                     'camera_side_screw_pattern':'Vertical pair' if p.CameraSideBoltSpacing else 'Single pivot',
                     'camera_vertical_screw_pitch_mm':p.CameraSideBoltSpacing,
                     'camera_side_hole_diameter_mm':p.CameraSideHoleDiameter,
                     'camera_pivot':'Upper side screw' if p.CameraTiltMechanism=='Upper pivot + lower arc' and p.CameraSideBoltSpacing and p.CameraMountMode=='Variable' else 'Camera centre',
                     'camera_adjustment':p.CameraTiltMechanism if p.CameraSideBoltSpacing and p.CameraMountMode=='Variable' else
                                         'Two fixed screw holes' if p.CameraMountMode=='Fixed' else 'Single-screw friction pivot; no mechanical end stops',
                     'camera_position_mode':p.CameraPositionMode,'camera_centre_y_mm':camera_position_y(p),
                     'camera_centre_height_mm':camera_pivot_height(p),'side_plates_follow_ends':p.CameraFollowPlates,
                     'camera_lower_attachment_mode':p.CameraBaseMode,
                     'camera_lower_extensions_mm':dict(zip(('rear','front'),camera_base_extensions(p))),
                     'camera_top_rearward_offset_mm':p.CameraTopRearOffset,'camera_tab_slots':camera_slots(p),'camera_top_tab_slots':camera_slots(p,'TopPlate'),
                     'top_front_profile':dict(shape=p.TopFrontShape,depth_mm=p.TopFrontDepth,recess_width_mm=p.TopFrontRecessWidth,clearance_mm=p.TopFrontClearance,shoulder_setback_mm=p.TopFrontSetback),'top_rear_front_bounds_mm':top_bounds(p),
                     'vtx_pattern':p.VTXPattern,'vtx_mounting_holes':[
                         {'point':point,'diameter_mm':2*radius,'spacing_mm':spacing}
                         for point,radius,spacing in vtx_holes(p)],
                     'vtx_mount_height_mm':0.} if p.FPVEnabled else None),
        }, indent=2) + "\n", encoding="utf-8")
        (folder / "READ_ME_FIRST.txt").write_text(
            "RotorForge manufacturing export\n\n"
            "All dimensions and DXF insertion units are millimetres. SVG physical dimensions are in mm.\n"
            "CuttingProfiles contains one profile for each physical carbon part, plus a combined sheet.\n"
            "Cutting profiles contain no text, labels or dimensions that could become accidental toolpaths.\n"
            "Stock_<thickness>.dxf / .svg separate the parts by stock thickness at 1:1 millimetre scale.\n"
            "Arms form one side-by-side row, alternating motor ends up/down, with 4 mm bounding-box gaps.\n"
            "Arms are rotated, never mirrored. Other parts retain flattened axes with 12 mm gaps; sheet margins are 10 mm.\n"
            "Layout.json records exact sheet origins, dimensions and part placements.\n"
            "The native FreeCAD Cutting profiles group contains one exact planar face per part, including holes.\n"
            "Stock subgroups match the local XY coordinates of their stock files; the root is placed beside the assembly.\n"
            "Re-export refreshes this snapshot. Save the FreeCAD document to retain it. Undo restores the prior snapshot.\n"
            "This is a spaced layout, not optimized nesting or a CAM job. Verify available stock, cutter clearance and fibre direction.\n"
            "No kerf, cutter radius compensation, dogbones, or machining tolerance was applied.\n"
            "Use CAM compensation; verify holes, tool access, dimensions, and fastener engagement.\n"
            f"The STEP contains assembled carbon parts, {2 * standoff_pair_count(p)} standoff tubes and the optional LiPo pad.\n"
            "LiPoPad files are separate-material STL/STEP and ungrooved DXF/SVG outlines, not carbon nesting. Scaled-pad spline edges in DXF/SVG use line segments with 0.01 mm chord deflection; STEP retains CAD curves.\n"
            "MassProperties.json includes bare-frame and nominal equipped/loaded estimates with calculation scope. EquipmentMass.csv itemizes all equipment and screw assumptions when enabled.\n"
            "PartsList.csv mass is per item; multiply by Quantity. Blank masses have not been assigned.\n"
            "Bare frame excludes electronics. Equipped estimates include editable motor/prop/FC/ESC/FPV masses, size-based screws and Other equipment allowance. These are planning estimates, not measured aircraft values.\n"
            "Prop, motor, and electronics references are excluded. No actual motors or PCBs are supplied.\n"
            "Motor patterns rotate with each arm; arm names are physical positions, not Betaflight motor numbers.\n"
            + ("Three plates: bottom / arms / mid sandwich. The bottom extends forward and the mid body runs stack-to-rear.\n"
               "Front arm clamp tabs are integrated into the mid plate. Shared arm standoffs sit on the mid, including the front tabs.\n"
               "Free bottom-mounted standoffs are longer by arm plus mid thickness. See the parts list for actual lengths.\n"
               if three_plate(p) else 'Two plates: arms '+p.TwoPlateArmPosition.lower()+'. No mid plate is included.\n')
            + ('One continuous arm clamp connects all four arm roots on the side opposite the bottom plate.\n'
               'Above-bottom arms use an upper clamp/FC deck; below-bottom arms use only a lower clamp.\n'
               'The eight existing root bolts secure it; clamp grip includes the complete sandwich.\n' if arm_braces(p) else '')
            + ('The central keystone follows all four arm seats and uses the same stock thickness as the arms.\n'
               'Fit the key with the arms; stack access reliefs stay open through the key.\n'
               'Keystone edge clearance is nominal geometry. Apply appropriate manufacturing fit allowances.\n'
               if keystone_active(p) else '')
            + ('A lower capture plate holds the underside arms and key against the bottom. The eight arm bolts secure\n'
               'lower clamp / arms and optional key / bottom. The FC stack mounts on the bottom plate.\n'
               'No point-retainer screws or secondary key countersinks are required.\n' if underside_clamp_active(p) else '')
            + ('Below-bottom key: two retaining screws pass through clamp, bottom and key, with nuts underneath.\n'
               'IMPORTANT: flat DXF/SVG contain the smaller THROUGH holes only. Machine the two upper-face\n'
               '90-degree clamp countersinks in MachiningOps.csv so the screw heads are flush under the stack.\n'
               'STEP/native solids already include these countersinks. CSV gives both frame XY and individual DXF XY.\n'
               if machining else '')
            + "Pairs mount on the mid or combined clamp where supported; otherwise they span bottom-to-top.\n"
            "ExportInfo.json records the position, mounting plate, and length of every standoff.\n"
            "Shared arm mounts use one coaxial hole through the complete arm sandwich into a standoff; top screws attach the top.\n"
            "Standoff bases follow the actual bottom, arm, mid or combined clamp support.\n"
            "Clamp-bolt grip excludes thread engagement. Shared fasteners are counted once.\n"
            "Stack screws and spacers must suit the selected plate arrangement.\n"
            +f"The FC stack mounts on {stack_mounting_role(p)} using {p.StackHoleDiameter:g} mm holes.\n"
            +('The bottom has '+f'{p.StackAccessDiameter:g} mm screw-head access holes, aligned through intervening arm/key material.\n'
              if three_plate(p) or upper_clamp_active(p) else 'Lower clamp stack openings provide screw access to the bottom plate.\n' if underside_clamp_active(p) else '')
            +('Top plate battery strap openings: '+(p.StrapOpeningStyle if p.StrapSlotsEnabled else 'None')+'.\n')
            +
            "Carbon mass estimate excludes all hardware and electronics. No strength or vibration analysis.\n"
            + ("FPV mode: CameraPlates contains separate STEP and flat STL files for the two side plates.\n"
               "The side plates are included in FrameAssembly.step and in the flat carbon DXF/SVG sheets.\n"
               "Lower and upper tongues fit matching rounded slots in the bottom and top plates.\n"
               "Assemble the side plates before bolting down the top; tab clearance is configurable.\n"
               "Camera side screws form a vertical pair when the camera is level; pitch and camera width are independent.\n"
               "Variable tilt uses a single friction pivot, upper/lower centred arc slots, or a fixed upper pivot plus lower arc.\n"
               "Fixed tilt uses two vertically spaced camera side screws on each side. Single-screw pivots have no mechanical end stops.\n"
               "Dual arc slots hold the body centre stationary. The alternative round pivot hole is the upper screw.\n"
               "Position the camera automatically in the side plates or set a custom body centre Y and height.\n"
               "Upper and lower tongues have independent coordinates; side plates slope to follow different plate ends.\n"
               "Custom lower attachment extensions widen only the bottom contact edge; its tongues and receiving slots follow the new length.\n"
               "The top has an open front camera cutout, retaining both upper tab slots on each side.\n"
               "Automatic reach supports the camera and covers the VTX; Custom uses exact independent front/rear reaches.\n"
               "The three-plate bottom does not extend automatically to the rear VTX; the mid carries it independently.\n"
               "Camera body must clear the plates; the tilted lens may rise through the front cutout.\n"
               "Rear VTX holes are cut only in the bottom with two plates, or only in the mid with three.\n"
               "When both VTX patterns are present, install one set of four fasteners, not eight.\n"
               "The VTX reference sits directly on its carrier; match actual screw threads, lengths, and camera/VTX dimensions.\n"
               "Camera, lens, and VTX envelopes are approximate references and are excluded from STEP.\n"
               if p.FPVEnabled else "Non-FPV mode: camera side plates and FPV mounting holes are omitted.\n")
            + "\nAirflow cuts are included in the exact DXF/SVG, STEP, mass, and camera STL.\n"
            "Cutout patterns and coordinates are recorded in ExportInfo.json and FrameParameters.json.\n"
            "The stack reference uses the supporting plate upper face plus the explicit stack spacer height, with automatic press-nut clearance when selected.\n"
            + ("\nLayout notes:\n" + "\n".join(warnings) if warnings else ""), encoding="utf-8")
        from .cutting_layout import document_layout
        origin_x=max(shape.BoundBox.XMax for shape in shapes.values() if not shape.isNull())+30
        document_layout(settings,layout,profile_faces,folder/'CuttingProfiles',origin_x)
        return folder
    except Exception:
        # This function owns only this newly created folder.
        shutil.rmtree(folder)
        raise

