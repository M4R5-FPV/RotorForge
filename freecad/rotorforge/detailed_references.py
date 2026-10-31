"""Optional generic presentation solids. Full clearance probes stay independent.

Canonical models are cached by explicit dimensions, then copied/placed. Neither
this module nor OpenCASCADE is loaded by the live editor's plan-view renderer.
"""
from functools import lru_cache
import math
import FreeCAD as App,Part
BLACK=(.11,.125,.14);METAL=(.52,.55,.59);COPPER=(.68,.31,.12)
PCB=(.08,.32,.23);SILICONE=(.15,.17,.19);CHIP=(.075,.085,.09)
PROP=(.18,.57,.62);GLASS=(.12,.27,.36)
from .reference_options import (FLAGS,SIMPLE,enabled,SHAFT_DIAMETER,PROP_BORE,PROP_HUB_HEIGHT,LOCKNUT_AF,LOCKNUT_HEIGHT,blade_pitch_angle,shaft_top)
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,App.Vector(x,y,z))
def cyl(radius,height,x=0,y=0,z=0):return Part.makeCylinder(radius,height,App.Vector(x,y,z))
def ring(ro,ri,h,z=0,x=0,y=0):return cyl(ro,h,x,y,z).cut(cyl(ri,h+.02,x,y,z-.01))
def chamfer_box(w,d,h,z=0,corner=1):
 c=min(corner,w*.2,d*.2);x=w/2;y=d/2
 pts=[(-x+c,-y), (x-c,-y),(x,-y+c),(x,y-c),(x-c,y),(-x+c,y),(-x,y-c),(-x,-y+c)]
 vs=[App.Vector(a,b,z) for a,b in pts];return Part.Face(Part.makePolygon(vs+[vs[0]])).extrude(App.Vector(0,0,h))
def compound(items):
 shape=Part.makeCompound([s.copy() for s,c in items]);colours=tuple(c for s,c in items for f in s.Faces)
 return shape,colours

@lru_cache(maxsize=16)
def motor_model(d,h,bolt_circle=None,count=4,hole=3.2,phase=0.):
 r=d/2;items=[];foot_h=min(2.5,h*.15);bolt_radius=(bolt_circle if bolt_circle is not None else d*.75)/2
 toe=max(hole/2+.8,min(3.,r*.22));hub=min(r*.40,max(3.,r*.30))
 # Rounded radial feet support the actual mounting pattern, rather than a disc.
 foot=cyl(hub,foot_h);tools=[]
 for i in range(count):
  angle=phase+360*i/count;a=math.radians(angle);x,y=bolt_radius*math.cos(a),bolt_radius*math.sin(a)
  spoke=box(0,-toe,0,bolt_radius,2*toe,foot_h);spoke.rotate(App.Vector(),App.Vector(0,0,1),angle)
  foot=foot.fuse(spoke).fuse(cyl(toe,foot_h,x,y))
  tools.append(cyl(hole/2,foot_h+.2,x,y,-.1))
 tools.append(cyl(min(2.,r*.15),foot_h+.2,z=-.1));foot=foot.cut(Part.makeCompound(tools)).removeSplitter();items.append((foot,BLACK))
 # The pedestal must meet the grey annulus even on a small bolt circle.
 support_radius=min(r*.40,bolt_radius-hole/2-.5)
 if support_radius<=0:raise ValueError('Motor mounting screws leave no room for the central support.')
 # Stator and copper reach just below the bell roof, with visible radial lobes.
 items.append((ring(r*.53,min(r*.20,support_radius*.75),h*.60,h*.30),METAL))
 coil_z=h*.34  # Above the lower bell edge (.30h), clear of the feet.
 for i in range(12):
  a=2*math.pi*i/12;items.append((cyl(r*.12,h*.92-coil_z,r*.59*math.cos(a),r*.59*math.sin(a),coil_z),COPPER))
 # Dark bearing pedestal joins the feet to the stator at the bell floor.
 # Keep a radial 0.5 mm gap to every mounting-screw shank, independent of
 # its engagement length; screw heads sit below the mounting plane.
 items.append((ring(support_radius,min(r*.15,support_radius*.4),h*.30-foot_h,foot_h),BLACK))
 items.append((ring(r,r*.87,h*.64,h*.30),BLACK))
 items.append((ring(r*.99,r*.86,h*.06,h*.94),BLACK))
 items.append((cyl(min(r*.55,5.5),h*.10,z=h*.90),BLACK))
 for i in range(6):
  spoke=box(-r*.075,r*.19,h*.94,r*.15,r*.7,h*.06);spoke.rotate(App.Vector(),App.Vector(0,0,1),i*60);items.append((spoke,BLACK))
 # Smooth M5 shaft; no expensive helical thread geometry in a display model.
 items.append((cyl(SHAFT_DIAMETER/2,shaft_top(h)-h+.2,z=h-.2),METAL))
 nut_z=h+PROP_HUB_HEIGHT;cr=LOCKNUT_AF/math.sqrt(3)
 vertices=[App.Vector(cr*math.cos(i*math.pi/3),cr*math.sin(i*math.pi/3),nut_z) for i in range(6)]
 nut=Part.Face(Part.makePolygon(vertices+[vertices[0]])).extrude(App.Vector(0,0,LOCKNUT_HEIGHT-1.2))
 nut=nut.cut(cyl(SHAFT_DIAMETER/2,LOCKNUT_HEIGHT+.2,z=nut_z-.1));items.append((nut,BLACK))
 items.append((ring(3.8,3.1,1.2,nut_z+LOCKNUT_HEIGHT-1.2),BLACK))
 items.append((ring(3.1,SHAFT_DIAMETER/2,1.2,nut_z+LOCKNUT_HEIGHT-1.2),(.08,.13,.19)))
 return compound(items)

@lru_cache(maxsize=16)
def prop_model(d):
 r=d/2;hub=max(4.,min(8.,r*.105));thick=max(.3,min(1.3,r*.018))
 hubshape=ring(hub,PROP_BORE/2,PROP_HUB_HEIGHT)
 sections=[]
 # The section chord is tangential to the swept station's actual radius.
 # Its helix angle follows P = 2*pi*r*tan(beta), with P = 3.7 inches.
 stations=((hub*.70,min(r*.11,5.),0),(r*.56,r*.23,r*.10),(r*.90,r*.10,r*.18),(r*.965,r*.028,r*.20))
 for index,(radius,width,sweep) in enumerate(stations):
  rho=math.hypot(radius,sweep);a=blade_pitch_angle(rho)
  if index==0:width=min(width,(PROP_HUB_HEIGHT-thick-.4)/math.sin(a))
  centre=App.Vector(sweep,radius,PROP_HUB_HEIGHT/2)
  tangent=App.Vector(radius/rho,-sweep/rho,0);vertical=App.Vector(0,0,1)
  u=tangent*math.cos(a)+vertical*math.sin(a);v=tangent*(-math.sin(a))+vertical*math.cos(a);pts=[]
  for x,z in ((-width/2,-thick/2),(width/2,-thick/2),(width/2,thick/2),(-width/2,thick/2)):pts.append(centre+u*x+v*z)
  sections.append(Part.makePolygon(pts+[pts[0]]))
 blade=Part.makeLoft(sections,True,False);items=[(hubshape,PROP)]
 for i in range(3):
  b=blade.copy();b.rotate(App.Vector(),App.Vector(0,0,1),i*120);items.append((b,PROP))
 return compound(items)

def stack_dimensions(height):
 t=min(1.4,height*.12);cap=min(1.,height*.1);low=height*.15;high=height-cap-t
 return t,cap,low,high,(low+t+high)/2

@lru_cache(maxsize=16)
def stack_model(spacing,height,hole,usb_side="Left",usb_y=0.):
 w=spacing+6;t,cap,low,high,join=stack_dimensions(height);items=[]
 gouter=min(2.9,max(min(2.7,spacing*.12),hole/2+.8));neck=min(gouter-.3,max(gouter*.72,hole/2+.35));bore=min(hole/2,neck-.2)
 for upper,z in ((False,low),(True,high)):
  board=chamfer_box(w,w,t,z,min(2.,w*.08));tools=[]
  for x in (-spacing/2,spacing/2):
   for y in (-spacing/2,spacing/2):tools.append(cyl(neck,t+.1,x,y,z-.05))
  board=board.cut(Part.makeCompound(tools));items.append((board,PCB))
  for x in (-spacing/2,spacing/2):
   for y in (-spacing/2,spacing/2):
    base,end=(join,height) if upper else (0.,join)
    # Matching necks meet exactly between the PCBs. The FC neck points down;
    # only its short retaining flange lies above the top PCB, under the nut.
    neckbody=cyl(neck,end-base,x,y,base)
    below=cyl(gouter,cap,x,y,z-cap);above=cyl(gouter,cap,x,y,z+t)
    grommet=neckbody.fuse(below).fuse(above).cut(cyl(bore,end-base+.2,x,y,base-.1))
    items.append((grommet.removeSplitter(),SILICONE))
 for x in (-w*.28,w*.28):
  for y in (-w*.25,0,w*.25):items.append((box(x-w*.08,y-w*.07,low+t,w*.16,w*.14,min(height*.12,(high-low-t)*.5)),CHIP))
 items.extend(((box(-w*.13,-w*.12,high+t,w*.26,w*.24,cap*.9),CHIP),
               (box(w*.20,-w*.10,high+t,w*.10,w*.12,cap*.7),METAL),
               (box(-w*.16,w*.34,high+t,w*.32,w*.13,cap*.8),METAL)))
 # Generic side-facing USB-C receptacle: hollow metal shell and dark tongue.
 # Outer 9 x 3.2 mm face, 7.5 mm body, protruding 0.8 mm beyond the PCB.
 # These are reference dimensions, not a specific manufacturer's footprint.
 usb_z=high+t
 def socket_capsule(x,length,width,height,z):
  radius=height/2;span=width-height
  solid=box(x,usb_y-span/2,z,length,span,height)
  for yy in (usb_y-span/2,usb_y+span/2):
   solid=solid.fuse(Part.makeCylinder(radius,length,App.Vector(x,yy,z+radius),App.Vector(1,0,0)))
  return solid.removeSplitter()
 shell=socket_capsule(w/2-6.7,7.5,9.,3.2,usb_z)
 cavity=socket_capsule(w/2-6.4,7.6,8.2,2.5,usb_z+.35)
 shell=shell.cut(cavity)
 tongue=box(w/2-6.4,usb_y-3.2,usb_z+1.35,6.8,6.4,.5)
 for part,colour in ((shell,METAL),(tongue,CHIP)):
  if usb_side=='Left':part.rotate(App.Vector(0,usb_y,0),App.Vector(0,0,1),180)
  items.append((part,colour))
 for x in (-w*.38,w*.38):
  for y in (-w*.15,w*.05,w*.25):
   if (x<0)==(usb_side=='Left') and abs(y-usb_y)<5.5:continue
   items.append((box(x-w*.025,y,high+t,w*.05,w*.045,cap*.45),METAL))
 return compound(items)

@lru_cache(maxsize=16)
def vtx_model(w,l,h,holes,digital):
 t=min(1.2,h*.18);board=chamfer_box(w,l,t,corner=min(w,l)*.06)
 tools=[cyl(rad,t+.1,x,y,-.05) for x,y,rad in holes]
 if tools:board=board.cut(Part.makeCompound(tools))
 items=[(board,PCB)]
 shield=chamfer_box(w*.62,l*.62,h*.44,t,min(w,l)*.07);items.append((shield,METAL))
 # Low fins, RF sockets and a cable header remain within the selected envelope.
 z=t+h*.44
 for i in range(7):items.append((box(-w*.26+i*w*.08,-l*.24,z,w*.025,l*.48,min(h*.30,h-z)),BLACK))
 for x in ((-w*.16,w*.16) if digital else (0.,)):
  items.append((ring(min(w,l)*.045,min(w,l)*.023,h*.10,t,x,-l*.40),(.68,.49,.18)))
 items.append((box(-w*.22,l*.36,t,w*.44,l*.10,h*.18),BLACK))
 return compound(items)

@lru_cache(maxsize=16)
def lipo_model(w,l,h):
 lead=min(12.,l*.18);length=l;body=chamfer_box(w*.992,length-2*l*.035,h*.98,corner=min(w,l)*.09);items=[(body,(.82,.34,.07))]
 # Shrink-wrap end protection, cell seam lines and a printed top label.
 for y in (-l/2,-l/2+length-l*.035):items.append((box(-w*.49,y,.03*h,w*.98,l*.035,h*.94),BLACK))
 for i in range(1,6):
  for x in (-w/2,w/2-w*.004):items.append((box(x,-l/2+l*.04,h*i/6,w*.004,length-l*.08,h*.007),(.34,.22,.15)))
 items.append((box(-w*.32,-length*.25,h-.08*h,w*.64,length*.5,.077*h),BLACK))
 items.append((box(-w*.22,-length*.20,h-.005*h,w*.44,length*.09,.005*h),(.75,.77,.78)))
 # Schematic leads exit the nominal pack body; they are not a routing model.
 plug_w=min(w*.36,12.);plug_h=min(h*.28,8.);wire_r=min(1.2,w*.025,h*.04);z=h*.58
 for x,c in ((-plug_w*.22,(.65,.06,.04)),(plug_w*.22,BLACK)):
  items.append((Part.makeCylinder(wire_r,lead*.68+.1,App.Vector(x,l/2-.1,z),App.Vector(0,1,0)),c))
 plug=chamfer_box(plug_w,lead*.36,plug_h,z-plug_h/2,min(1.,plug_w*.12));plug.translate(App.Vector(0,l/2+lead*.82,0));items.append((plug,(.76,.53,.13)))
 # Frame front is +Y: put the leads at the rear before user rotation.
 shape,colours=compound(items)
 shape.rotate(App.Vector(),App.Vector(0,0,1),180)
 return shape,colours

@lru_cache(maxsize=16)
def camera_model(w,d,h,spacing,hole):
 body=chamfer_box(w,h,d,0,min(w,h)*.12)
 # Canonical housing is extruded along Z, then turned to face frame +Y.
 body.rotate(App.Vector(),App.Vector(1,0,0),-90);body.translate(App.Vector(0,-d/2,0))
 radius=min(6.,w*.35,h*.35);items=[]
 # Side screw recesses model the existing vertical camera fixing convention.
 for side in (-1,1):
  for z in ((-spacing/2,spacing/2) if spacing else (0.,)):
   tool=Part.makeCylinder(min(hole/2,h*.08),w*.09,App.Vector(side*(w/2+.01),0,z),App.Vector(-side,0,0));body=body.cut(tool)
 items.append((body,BLACK))
 bezel=chamfer_box(w*.9,h*.9,min(.35,d*.04),0,min(w,h)*.1)
 bezel.rotate(App.Vector(),App.Vector(1,0,0),-90);bezel.translate(App.Vector(0,d/2-min(.35,d*.04),0))
 # Remove the insert stock from the housing: no coplanar double faces.
 items[0]=(body.cut(bezel),BLACK)
 items.append((bezel,(.22,.24,.26)))
 for rad,start,length,colour in ((radius,d/2-.05,1.2,METAL),(radius*.86,d/2+1.15,3.0,BLACK),(radius*.95,d/2+4.15,1.6,BLACK),(radius*.76,d/2+5.75,.25,GLASS)):
  items.append((Part.makeCylinder(rad,length,App.Vector(0,start,0),App.Vector(0,1,0)),colour))
 return compound(items)

def detailed_reference(p,role):
 from .parameters import arms_above_bottom,motor_centres,stack_reference_z,arm_layouts
 from .motor_pads import motor_pad_unit
 items=[];colours=[]
 if role in ('MotorEnvelopes','PropellerDiscs'):
  motor=role=='MotorEnvelopes';model,c=motor_model(p.MotorReferenceDiameter,p.MotorReferenceHeight,p.MotorBoltCircle,3 if p.MotorHoleLayout.startswith('3') else 4,p.MotorHoleDiameter,p.MotorHoleRotation) if motor else prop_model(p.PropDiameter)
  z=(p.BottomThickness if arms_above_bottom(p) else -p.ArmThickness)+p.ArmThickness+(0 if motor else p.MotorReferenceHeight)
  arms=arm_layouts(p) if motor else ()
  for i,(x,y) in enumerate(motor_centres(p)):
   shape=model.copy()
   if not motor and i%2:
    transform=App.Matrix();transform.A11=-1;shape=shape.transformGeometry(transform)
   angle=math.degrees(math.atan2(*reversed(motor_pad_unit(p,arms[i])))) if motor else (30 if i%2 else -30)
   shape.rotate(App.Vector(),App.Vector(0,0,1),angle);shape.translate(App.Vector(x,y,z));items.append(shape);colours.extend(c)
 elif role=='StackEnvelope':
  shape,c=stack_model(p.StackSpacing,p.StackHeight,p.StackHoleDiameter,p.StackUSBFace,p.StackUSBOffsetY);shape=shape.copy();shape.translate(App.Vector(0,p.StackOffsetY,stack_reference_z(p)));items.append(shape);colours.extend(c)
 elif role=='VTXEnvelope':
  from .fpv import vtx_holes,vtx_deck_z
  holes=tuple((x,y-p.VTXOffsetY,rad) for (x,y),rad,pattern in vtx_holes(p))
  shape,c=vtx_model(p.VTXWidth,p.VTXLength,p.VTXHeight,holes,p.VideoSystem=='Digital');shape=shape.copy();shape.translate(App.Vector(0,p.VTXOffsetY,vtx_deck_z(p)));items.append(shape);colours.extend(c)
 elif role=='BatteryEnvelope':
  from .battery import battery_levels
  shape,c=lipo_model(p.BatteryWidth,p.BatteryLength,p.BatteryHeight);shape=shape.copy()
  if p.BatteryMount=='Bottom plate':shape.rotate(App.Vector(0,0,p.BatteryHeight/2),App.Vector(0,1,0),180)
  shape.rotate(App.Vector(),App.Vector(0,0,1),p.BatteryRotation);shape.translate(App.Vector(p.BatteryX,p.BatteryY,battery_levels(p)['battery_z']));items.append(shape);colours.extend(c)
 elif role=='CameraEnvelope':
  from .fpv import camera_body_centre
  shape,c=camera_model(p.CameraWidth,p.CameraBodyDepth,p.CameraHeight,p.CameraSideBoltSpacing,p.CameraSideHoleDiameter);shape=shape.copy();shape.rotate(App.Vector(),App.Vector(1,0,0),p.CameraTilt);shape.translate(App.Vector(0,*camera_body_centre(p)));items.append(shape);colours.extend(c)
 return Part.makeCompound(items),tuple(colours)

def apply_reference_material(view,role,p):
 """Reset simple colours on disable, and apply cached per-face model colours."""
 if role not in FLAGS:return
 detailed=enabled(p,role)
 base,trans=SIMPLE[role];colours=(base,)
 if detailed:
  base=PROP if role=='PropellerDiscs' else PCB if role in ('StackEnvelope','VTXEnvelope') else (.82,.34,.07) if role=='BatteryEnvelope' else BLACK
  trans=8 if role=='PropellerDiscs' else 0
  # Construction only happens during document updates, never live editor paint.
  if p.ShowReferences and (role not in ('CameraEnvelope','VTXEnvelope') or p.FPVEnabled) and (role!='BatteryEnvelope' or p.BatteryReferenceEnabled):_,colours=detailed_reference(p,role)
 view.ShapeColor=base;view.LineColor=(.08,.09,.10)
 view.DiffuseColor=list(colours);view.Transparency=trans

