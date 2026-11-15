"""Conservative, FreeCAD-independent broad phase for tilted camera checks.

A rotated axis-aligned box always encloses the rotated detailed BRep it
bounds. Rejecting an angle here is therefore safe; potential contacts always
use the exact native FreeCAD Boolean intersection and existing validation.
"""
import math


def rotated_camera_aabb(local, angle_degrees, centre):
    """Bounds after +X rotation and (0,centre_y,centre_z) translation.

    local is (xmin,xmax,ymin,ymax,zmin,zmax) of the *entire* fused local
    camera (housing and lens). Use all four Y/Z extreme corners, not just a
    pair of corners; one-corner approximations can miss a rotated lens.
    """
    xmin,xmax,ymin,ymax,zmin,zmax=local
    radians=math.radians(float(angle_degrees))
    c,s=math.cos(radians),math.sin(radians)
    ys=(y*c-z*s for y in (ymin,ymax) for z in (zmin,zmax))
    zs=(y*s+z*c for y in (ymin,ymax) for z in (zmin,zmax))
    y_values=tuple(ys)
    z_values=tuple(zs)
    cy,cz=centre
    return (xmin,xmax,min(y_values)+cy,max(y_values)+cy,
            min(z_values)+cz,max(z_values)+cz)


def aabbs_may_overlap(a,b,margin=1.e-5):
    """A conservative reject: touching and nearly touching boxes pass."""
    return not (a[1]<b[0]-margin or b[1]<a[0]-margin or
                a[3]<b[2]-margin or b[3]<a[2]-margin or
                a[5]<b[4]-margin or b[5]<a[4]-margin)


def as_tuple(b):
    """Copy the six native BoundBox scalars, without holding OCC objects."""
    return (float(b.XMin),float(b.XMax),float(b.YMin),float(b.YMax),
            float(b.ZMin),float(b.ZMax))
