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

def vtx_reference_kind(digital,style='Automatic'):
 """Resolve the exact *exclusive* transmitter style, independent of CAD state."""
 if style == 'Automatic':
  return 'digital' if digital else 'analog_enclosed'
 return {'Exposed PCB':'analog_exposed',
         'Finned enclosure':'digital',
         'Analog enclosed':'analog_enclosed'}[style]

@lru_cache(maxsize=24)
def vtx_model(w,l,h,holes,digital,style='Automatic'):
 """Self-contained, product-inspired FPV transmitter presentation reference.

 The three mutually exclusive branches prevent any shared analog detailing
 from appearing on the digital unit. All subparts are supported by either the
 main body or PCB; former z-gaps under shield cans, chips and sockets are gone.
 Models are illustrative rather than exact manufacturer CAD.
 """
 kind=vtx_reference_kind(digital,style)
 gold=(.73,.50,.16);silver=(.66,.69,.72)
 dark=(.11,.12,.135);anodised=(.17,.185,.205)
 lid=(.24,.255,.27);rib=(.30,.32,.34)
 board_green=(.052,.21,.17);board_black=(.058,.080,.087)
 chip=(.067,.075,.08);white=(.82,.82,.77);ceramic=(.55,.44,.29)
 copper=(.67,.39,.15);indicator=((.65,.10,.095),(.08,.54,.14),(.13,.30,.62))
 items=[]
 through=tuple((x,y,rad,Part.makeCylinder(rad+.025,h+.2,App.Vector(x,y,-.1))) for x,y,rad in holes)
 def add(shape,colour,clear=True):
  if clear and through:
   bb=shape.BoundBox
   cutters=[tool for x,y,rad,tool in through if
    bb.XMin<x+rad+.025 and bb.XMax>x-rad-.025 and
    bb.YMin<y+rad+.025 and bb.YMax>y-rad-.025]
   if cutters:shape=shape.cut(Part.makeCompound(cutters))
  if not shape.isNull():items.append((shape,colour))

 # Details at the case edges are machined clear, so side connectors remain
 # visibly accessible rather than becoming swallowed by an opaque housing.
 rr=min(1.18 if kind=='digital' else 1.49,h*.16,w*.065)
 rf_depth=min(2.35,l*.16)
 rf_positions=(-w*.235,w*.235) if kind=='digital' else (0.,)
 hw=min(8.5,w*.27);hd=min(3.05,l*.125)
 hh=min(2.25,h*.25)
 front_hz=h*.19
 hy=l*.5-hd-.045
 def machined_housing(s):
  for x in rf_positions:
   tool=Part.makeCylinder(rr*1.045,rf_depth+.38,
       App.Vector(x,-l*.5-.12,h*.43),App.Vector(0,1,0))
   s=s.cut(tool)
  s=s.cut(box(-hw*.54,hy-.08,front_hz-.12,
              hw*1.08,hd+.18,hh+.27))
  if kind=='digital':
   s=s.cut(box(w*.15,l*.33,h*.30,w*.21,l*.18,h*.18))
  return s

 # Use one full-height board/enclosure per branch. No analog base PCB is
 # retained under the digital reference, even when updating an older frame.
 if kind=='analog_exposed':
  t=min(1.20,max(.5,h*.15))
  body=chamfer_box(w,l,t,0,min(w,l)*.065)
  add(body,board_green)
  # Exposed commercial RF board: a broad stamped shield at the RF side,
  # discrete PA and controller, densely populated small passives and header.
  shield_h=min(h*.40,3.15);shield_z=t-.035
  add(chamfer_box(w*.53,l*.46,shield_h,shield_z,min(.8,w*.024)),silver)
  # Raised stamped seam is seated on the RF can (not a floating insert).
  add(chamfer_box(w*.45,l*.375,min(.11,h*.02),shield_z+shield_h-.035,
                  min(.5,w*.018)),(.54,.57,.59))
  # Adjacent PA and power stage lie on the same top surface as the PCB.
  add(box(-w*.17,-l*.425,t-.03,w*.34,l*.135,min(h*.21,1.4)),dark)
  for x,y,sx,sy in ((-w*.34,-l*.11,w*.135,l*.13),
                    (w*.34,-l*.11,w*.135,l*.13),
                    (-w*.32,l*.24,w*.14,l*.11),
                    (w*.31,l*.25,w*.14,l*.105)):
   height=min(h*.17,1.35)
   add(box(x-sx/2,y-sy/2,t-.03,sx,sy,height),chip)
   # Package mould mark lies directly atop the body.
   add(box(x-sx*.24,y-sy*.13,t-.03+height-.015,sx*.48,sy*.26,.025),rib)
  for sign in (-1,1):
   for j in range(6):
    x=(w*.405 if sign>0 else -w*.435)
    y=-l*.12+j*l*.067
    add(box(x,y,t-.025,w*.035,l*.026,min(.42,h*.06)),white if j%3 else ceramic)
  # SMT footprints and front-edge status indicators (LEDs sit on the PCB).
  for j in range(3):
   add(box(-w*.18+j*w*.09,l*.38,t-.020,w*.038,l*.027,.04),gold)
   add(cyl(min(.31,w*.010),min(.19,h*.024),
           -w*.17+j*w*.09,l*.315,t-.02),indicator[j])
  add(box(w*.31,l*.31,t-.025,w*.075,l*.065,min(.52,h*.07)),dark)
  # Low annular copper around the actual through holes.
  for x,y,rad in holes:
   edge=min(w*.5-abs(x),l*.5-abs(y));outer=min(rad+.5,edge-.08)
   if outer>rad+.06:add(ring(outer,rad+.03,.046,t-.018,x,y),gold,False)
  # RF connector support extends down to PCB; the end barrel is horizontal.
  port_z=t+min(.68,(h-t)*.16)
  mount_h=min(1.55,(h-t)*.44)
  add(box(-w*.094,-l*.49,t-.035,w*.188,l*.16,mount_h),dark)
 else:
  # Enclosed units are opaque CNC-style metal housings with no exposed
  # analog circuit-board base, loose ICs or detached copper pads.
  if kind=='analog_enclosed':
   # Inspired by enclosed Foxeer / RUSH analog VTX designs: squat dark slab,
   # one rear RF output, front control header and modest cooling grooves.
   add(machined_housing(chamfer_box(w,l,h*.76,0,min(w,l)*.075)),dark)
   top_z=h*.76-.045
   add(chamfer_box(w*.944,l*.92,h*.155,top_z,min(w,l)*.054),anodised)
   # Shallow edge ridges, not the broad field of fins used by a digital unit.
   for j in range(6):
    x=-w*.30+j*w*.12
    add(box(x,-l*.26,top_z+h*.155-.02,w*.018,l*.46,
            min(h*.038,.30)),rib)
   # Inset power/status strip (black bezel with three actual LEDs).
   add(box(-w*.34,l*.19,top_z+h*.156-.03,w*.28,l*.07,
           min(h*.033,.26)),lid)
   for j,c in enumerate(indicator):
    add(cyl(min(.39,w*.014),min(h*.018,.14),
            -w*.265+j*w*.075,l*.225,top_z+h*.156-.02),c)
   # Real analog VTX frequently includes a tiny channel/power mode switch.
   add(box(w*.27,l*.255,h*.68,w*.085,l*.07,h*.06),anodised)
   add(box(w*.294,l*.274,h*.735,w*.035,l*.036,min(.22,h*.025)),silver)
   port_z=h*.43
  else:
   # Walksnail-style digital slab with a densely ribbed heat spreader.
   add(machined_housing(chamfer_box(w,l,h*.78,0,min(1.8,w*.06,l*.06))),dark)
   top_z=h*.78-.055
   add(chamfer_box(w*.90,l*.90,h*.10,top_z,min(1.4,w*.05)),anodised)
   for j in range(15):
    x=-w*.33+j*w*.66/14
    add(box(x-w*.006,-l*.33,top_z+h*.10-.03,w*.012,l*.66,
            min(h*.055,.55)),rib)
   # A front-facing camera/data socket unique to digital transmitters.
   add(box(w*.16,l*.34,h*.31,w*.19,l*.13,h*.16),dark)
   add(box(w*.186,l*.445,h*.346,w*.13,l*.016,h*.073),silver)
   # Gold contacts are recessed in the digital socket, not analog test pads.
   for j in range(4):
    add(box(w*(.198+.027*j),l*.447,h*.356,w*.013,l*.01,h*.029),gold)
   port_z=h*.43

 # RF connections are built for this branch only. Their plastic support is
 # anchored in the underlying body, not separated from it by a z gap.
 for x in rf_positions:
  if kind=='analog_exposed':
   # PCB-footprint housing physically supports the MMCX barrel.
   add(box(x-rr*1.1,-l*.49,t-.045,rr*2.2,l*.18,
           max(.16,port_z+rr-t+.055)),dark)
  outer=Part.makeCylinder(rr,rf_depth,App.Vector(x,-l*.5+rf_depth+.015,port_z),App.Vector(0,-1,0))
  inner=Part.makeCylinder(rr*.53,rf_depth+.05,App.Vector(x,-l*.5+rf_depth+.04,port_z),App.Vector(0,-1,0))
  add(outer.cut(inner),gold)
  # Recessed dielectric/captive pin within the metal barrel.
  add(Part.makeCylinder(rr*.37,.18,App.Vector(x,-l*.5+.17,port_z),App.Vector(0,1,0)),dark)
  add(Part.makeCylinder(rr*.15,.15,App.Vector(x,-l*.5+.17,port_z),App.Vector(0,1,0)),silver)

 # Front/side power header: a real contact housing inset into its chassis or
 # seated on the bare PCB; never a detached connector hovering in midair.
 hz=(t-.04) if kind=='analog_exposed' else front_hz
 add(box(-hw*.5,hy,hz,hw,hd,hh),white if kind!='digital' else dark)
 add(box(-hw*.40,l*.5-hd*.24,hz+hh*.25,hw*.80,hd*.16,hh*.43),
     chip if kind!='digital' else silver)
 for j in range(5):
  x=-hw*.285+j*hw*.14
  add(box(x,l*.5-hd*.18,hz+hh*.37,hw*.05,hd*.065,hh*.12),gold)
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
  shape,c=vtx_model(p.VTXWidth,p.VTXLength,p.VTXHeight,holes,p.VideoSystem=='Digital',p.VTXReferenceStyle);shape=shape.copy();shape.translate(App.Vector(0,p.VTXOffsetY,vtx_deck_z(p)));items.append(shape);colours.extend(c)
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
  base=PROP if role=='PropellerDiscs' else (BLACK if role=='VTXEnvelope' and vtx_reference_kind(p.VideoSystem=='Digital',p.VTXReferenceStyle)!='analog_exposed' else PCB) if role in ('StackEnvelope','VTXEnvelope') else (.82,.34,.07) if role=='BatteryEnvelope' else BLACK
  trans=8 if role=='PropellerDiscs' else 0
  # Construction only happens during document updates, never live editor paint.
  if p.ShowReferences and (role not in ('CameraEnvelope','VTXEnvelope') or p.FPVEnabled) and (role!='BatteryEnvelope' or p.BatteryReferenceEnabled):_,colours=detailed_reference(p,role)
 view.ShapeColor=base;view.LineColor=(.08,.09,.10)
 # Explicitly replace the complete material array; no face colouring from the
 # preceding VTX style may survive a switch between analog and digital.
 view.DiffuseColor=[base]
 view.DiffuseColor=list(colours);view.Transparency=trans

