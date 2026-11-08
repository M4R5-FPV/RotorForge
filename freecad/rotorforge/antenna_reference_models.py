"""Optional native 3D antenna presentation references, not RF simulations.

All placements derive from the existing TPU holder/hook layout. A video antenna
has a slim cable or rigid stem plus a short enlarged radome at its far end;
the previous thick, full-length cylinder was visually incorrect. Antenna
cable/feed length is shown straight for approximate assembled appearance only.
"""
import FreeCAD as App
import Part
from .antenna_layout import antenna_layout
from .elrs_layout import elrs_layout
from .antenna_preset_specs import vtx_spec,elrs_spec,elrs_feed_to_vtx
from .antenna_reference_models_palette import VTX_HEAD_COLOURS

VTX_COLOUR=(.105,.110,.118)  # matte-black strain relief and plastic socket
ELRS_COLOUR=(.035,.039,.045)  # near-black rubber antenna housing
ELRS_HUB_COLOUR=(.047,.052,.059)
COAX_COLOUR=(.043,.047,.055)  # coax is darker than the default VTX radome
METAL=(.50,.54,.57)
RING=(.39,.30,.16)



def _compound(parts):
    if not parts:
        return Part.Shape(), ()
    return (Part.makeCompound([shape for shape, colour in parts]),
            tuple(colour for shape, colour in parts for _ in shape.Faces))


def _vtx_parts(p,holder,layout,spec):
    axis=App.Vector(*holder['axis'])
    start=App.Vector(*holder['start'])
    total=spec['length']
    head_radius=spec['head_diameter']/2.
    head_height=min(spec['head_length'], total*.42)
    cable_radius=max(.7,min(1.3,layout['bore']*.27))
    cable_height=total-head_height
    head_base=start+axis*cable_height
    parts=[]
    head_colour=VTX_HEAD_COLOURS[p.VTXAntennaHeadColour]
    # Most of the visible length is a slender RF lead, not the radome.
    parts.append((Part.makeCylinder(cable_radius,cable_height,start,axis),COAX_COLOUR))
    # Reinforcement/strain relief near the holder exit. Keep inside its bore.
    boot_start=start+axis*max(0.,layout['length']-1.5)
    boot_height=min(6.,max(0.,cable_height-(layout['length']-1.5)))
    if boot_height>0.1:
        parts.append((Part.makeCylinder(min(layout['bore']*.45, max(cable_radius,1.7)),
                                        boot_height,boot_start,axis),VTX_COLOUR))
    # Small flare into a short, wide cap; the upper end has a rounded crown.
    flare=min(3.,head_height*.23)
    parts.append((Part.makeCone(min(head_radius*.55,max(cable_radius,1.4)),head_radius,
                                flare,head_base,axis),head_colour))
    crown=min(head_radius, (head_height-flare)*.70)
    straight=max(.05,head_height-flare-crown)
    parts.append((Part.makeCylinder(head_radius,straight,head_base+axis*flare,axis),head_colour))
    parts.append((Part.makeSphere(crown,head_base+axis*(head_height-crown)),head_colour))
    # A small collar makes the transition readable, not a band all along the body.
    parts.append((Part.makeCylinder(min(head_radius*.85,max(1.,cable_radius*1.2)),
                                    min(1.2,flare*.5),head_base,axis),RING))
    if layout['bulkhead']:
        # Simplified SMA/RP-SMA retention ring at the printed tab. Not a thread.
        face=start+axis*(layout['length']-.3)
        parts.append((Part.makeCylinder(max(cable_radius+1.,layout['bore']*.51),1.,
                                        face,axis),METAL))
    return parts


def _elrs_parts(p,layout,spec):
    """Compact dipole T body, slim arms and coax running towards the airframe."""
    span=spec['span']
    radius=p.FlexELRSAntennaDiameter/2.
    center=App.Vector(0,layout['y'],layout['z'])
    along=App.Vector(1,0,0)
    left=center-along*(span/2-radius)
    parts=[(Part.makeCylinder(radius,max(.1,span-2*radius),left,along),ELRS_COLOUR),
           (Part.makeSphere(radius,center-along*(span/2-radius)),ELRS_COLOUR),
           (Part.makeSphere(radius,center+along*(span/2-radius)),ELRS_COLOUR)]
    # Molded central junction is wider than the arms, not a single uniform rod.
    hub_width=min(10.,span*.24)
    hub_depth=max(3.5,min(5.5,2.0*radius))
    hub_height=max(3.,min(4.5,2.0*radius))
    parts.append((Part.makeBox(hub_width,hub_depth,hub_height,
                               center-App.Vector(hub_width/2,hub_depth/2,hub_height/2)),
                  ELRS_HUB_COLOUR))
    cable_start=center+App.Vector(0,hub_depth/2.,0)
    # A reference lead must never enter the schematic VTX board envelope.
    # Calculate a fresh free length on each rebuild from the actual VTX position.
    feed=elrs_feed_to_vtx(p,cable_start.y)
    if feed>0.01:
        cable_radius=max(.55,min(1.,radius*.50))
        parts.append((Part.makeCylinder(cable_radius,feed,cable_start,App.Vector(0,1,0)),COAX_COLOUR))
        parts.append((Part.makeCone(max(cable_radius,1.5),cable_radius,min(3.,feed),
                                    cable_start,App.Vector(0,1,0)),ELRS_HUB_COLOUR))
    return parts


def antenna_reference(p,role):
    if role=='VTXAntennaReference':
        if not p.FlexRearAntenna or not p.ShowVTXAntennaReference:
            return Part.Shape(), ()
        layout=antenna_layout(p)
        spec=vtx_spec(p)
        parts=[]
        for holder in layout['holders']:
            parts.extend(_vtx_parts(p,holder,layout,spec))
        return _compound(parts)
    if role=='ELRSTReference':
        if not p.FlexELRSEnabled or not p.ShowELRSTReference:
            return Part.Shape(), ()
        return _compound(_elrs_parts(p,elrs_layout(p),elrs_spec(p)))
    raise ValueError('Unknown display-only antenna reference: '+role)


def reference_enabled(p,role):
    return bool(p.ShowReferences and (
        (role=='VTXAntennaReference' and p.FlexRearAntenna and p.ShowVTXAntennaReference) or
        (role=='ELRSTReference' and p.FlexELRSEnabled and p.ShowELRSTReference)))
