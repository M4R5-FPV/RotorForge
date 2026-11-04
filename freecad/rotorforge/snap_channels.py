"""Side-entry slots with a narrow retaining throat and flared lead-in."""
import FreeCAD as App
import Part

def entry_tool(start,axis,outward,length,bore,radius,lip,reach=None):
 # Local X is across the throat, Y points toward the opening, Z follows the stem.
 across=outward.cross(axis);across.normalize()
 gap=bore-2*lip;neck=max(0.,radius-.6);reach=max(radius+1,reach or 0)
 points=[(-gap/2,0),(gap/2,0),(gap/2,neck),(gap/2+.6,radius+1),(gap/2+.6,reach),(-gap/2-.6,reach),(-gap/2-.6,radius+1),(-gap/2,neck)]
 origin=start-axis*.02
 points=[pt for i,pt in enumerate(points) if not i or pt!=points[i-1]]
 vs=[origin+across*x+outward*y for x,y in points]
 return Part.Face(Part.makePolygon(vs+[vs[0]])).extrude(axis*(length+.04))


def front_direction(axis):
 """Project frame front (+Y) into the stem cross-section."""
 n=App.Vector(0,1,0)-axis*axis.y
 if n.Length<1e-8:n=App.Vector(0,0,1) # A horizontal rearward tube has no front-facing radial normal.
 n.normalize();return n

def full_entry_tool(solid,start,axis,bore,radius,lip):
 """Open the full axial thickness at the clip, preserving the remote carrier."""
 n=front_direction(axis);b=solid.BoundBox
 corners=[App.Vector(x,y,z)-start for x in (b.XMin,b.XMax) for y in (b.YMin,b.YMax) for z in (b.ZMin,b.ZMax)]
 low=min(v.dot(axis) for v in corners)-1;high=max(v.dot(axis) for v in corners)+1
 reach=radius+1 # Stop at the clip mouth; do not slit the remote carrier.
 return entry_tool(start+axis*low,axis,n,high-low,bore,radius,lip,reach)
