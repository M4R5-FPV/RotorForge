"""Single-face extrusions for mount ribs; avoid chains of solid booleans."""
import math
import FreeCAD as App
import Part

def stroke_solid(points,r,z,h):
 normals=[];directions=[]
 for a,b in zip(points,points[1:]):
  dx,dy=b[0]-a[0],b[1]-a[1];n=math.hypot(dx,dy)
  directions.append((dx/n,dy/n));normals.append((-dy/n,dx/n))
 offsets=[normals[0]]
 for u,v in zip(normals,normals[1:]):
  d=1+u[0]*v[0]+u[1]*v[1]
  offsets.append(((u[0]+v[0])/d,(u[1]+v[1])/d))
 offsets.append(normals[-1])
 sides=[[App.Vector(p[0]+sign*r*n[0],p[1]+sign*r*n[1],z) for p,n in zip(points,offsets)] for sign in (1,-1)]
 left,right=sides;edges=[Part.makeLine(a,b) for a,b in zip(left,left[1:])]
 p=points[-1];d=directions[-1];edges.append(Part.Arc(left[-1],App.Vector(p[0]+r*d[0],p[1]+r*d[1],z),right[-1]).toShape())
 edges.extend(Part.makeLine(a,b) for a,b in zip(right[::-1],right[-2::-1]))
 p=points[0];d=directions[0];edges.append(Part.Arc(right[0],App.Vector(p[0]-r*d[0],p[1]-r*d[1],z),left[0]).toShape())
 face=Part.Face(Part.Wire(edges))
 if not face.isValid():
  # Extreme narrow curves can fold their inner offset. Retain the robust union.
  ribs=[capsule(a,b,r,z,h) for a,b in zip(points,points[1:])]
  return ribs[0].multiFuse(ribs[1:]).removeSplitter()
 return face.extrude(App.Vector(0,0,h))

def capsule(a,b,r,z,h):
 if math.dist(a,b)<1e-8:return Part.makeCylinder(r,h,App.Vector(*a,z))
 return stroke_solid([a,b],r,z,h)

def bulkhead_tab(width,thickness,start,axis):
 from .geometry import rounded_plate
 tab=rounded_plate(width,width,2.,0,thickness)
 tab.Placement=App.Placement(start,App.Rotation(App.Vector(0,0,1),axis))
 return tab
