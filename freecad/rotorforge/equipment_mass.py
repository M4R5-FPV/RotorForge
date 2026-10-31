"""Editable nominal equipment masses and size-dependent fastener estimates.

Masses are grams, centres are assembly millimetres. No display solids are used.
"""
import math
MASS_FIELDS=('MotorMass','PropMass','FCMass','ESCMass','VTXMass','CameraMass','OtherMass','ScrewMassScale')

def equipment_items(p):
 from .parameters import (arm_layouts,plate_levels,standoff_layouts,stack_holes,
                          stack_reference_z,arm_clamp_grip)
 from .fpv import camera_body_centre,vtx_deck_z,vtx_holes
 levels=plate_levels(p);items=[]
 def add(name,mass,point):items.append(dict(part=name,mass_g=mass,centre_mm=tuple(point)))
 def screw(name,diameter,length,point):
  # Steel socket-head approximation: 80% thread envelope + cylindrical head.
  mass=math.pi/4*(.8*diameter**2*length+(1.7*diameter)**2*.65*diameter)*7.85/1000
  add(name,mass*p.ScrewMassScale,point)
 armz=levels['arm_z'];stackz=stack_reference_z(p)
 stands=standoff_layouts(p)
 for arm in arm_layouts(p):
  x,y=arm['motor'];z=armz+p.ArmThickness
  add('Motor',p.MotorMass,(x,y,z+p.MotorReferenceHeight/2))
  add('Propeller',p.PropMass,(x,y,z+p.PropReferenceHeight))
  for pt in arm['motor_holes']:screw('Motor screw',max(1.0,p.MotorHoleDiameter-.2),p.ArmThickness+3,(*pt,z-1))
  for pt in arm['bolts']:
   if any(math.dist(pt,s['point'])<1e-6 for s in stands if s['shared_arm']):continue
   screw('Arm root screw',max(1.,p.RootHoleDiameter-.2),arm_clamp_grip(p)+3,(*pt,armz+p.ArmThickness/2))
 for stand in stands:
  pt=stand['point'];d=max(1.,p.StandoffHoleDiameter-.2)
  screw('Standoff top screw',d,p.TopThickness+4,(*pt,levels['top_z']))
  screw('Shared arm screw' if stand['shared_arm'] else 'Standoff base screw',d,
        (stand['grip_length'] if stand['shared_arm'] else p.BottomThickness)+4,(*pt,stand['base']))
 add('Flight controller',p.FCMass,(0,p.StackOffsetY,stackz+p.StackHeight*.75))
 add('4-in-1 ESC',p.ESCMass,(0,p.StackOffsetY,stackz+p.StackHeight*.25))
 for pt in stack_holes(p):
  screw('Stack screw',max(1.,p.StackHoleDiameter-.2),p.StackHeight+(stackz-levels["stack_deck_z"])+4,(*pt,stackz+p.StackHeight/2))
 if p.FPVEnabled:
  y,z=camera_body_centre(p);add('Camera',p.CameraMass,(0,y,z))
  add('VTX',p.VTXMass,(0,p.VTXOffsetY,vtx_deck_z(p)+p.VTXHeight/2))
  for side in (-1,1):
   for i in range(2 if p.CameraSideBoltSpacing else 1):screw('Camera screw',max(1.,p.CameraSideHoleDiameter-.2),p.CameraBracketThickness+2,(side*p.CameraWidth/2,y,z+(i-.5)*p.CameraSideBoltSpacing))
  # Both-pattern drilling still receives one board with four screws.
  for pt,r,_ in vtx_holes(p)[:4]:screw('VTX screw',max(1.,2*r-.2),4.,(*pt,vtx_deck_z(p)/2))
 add('Other equipment / wiring',p.OtherMass,(0,p.StackOffsetY,stackz+p.StackHeight/2))
 return items
