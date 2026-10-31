"""Lightweight material colors shared by the native model and editor previews."""
from .flex_options import FLEX_ROLES
CARBON_COLOR=(.18,.19,.20)
CARBON_HEX='#2e3033'
CARBON_EDGE='#111315'
PAD_COLOR=(23/255,25/255,28/255)
PAD_HEX='#17191c'
PAD_GROOVE='#43464a'
PRINTED_COLOURS={
 'Black':'#17191c','Orange':'#ef751c','Red':'#d93636','Blue':'#2784d1',
 'Teal':'#25a6a2','Lime green':'#97cf36','Purple':'#8e54b8',
 'Yellow':'#f2ce35','White':'#e9ecef','Grey':'#808890'}
def printed_hex(p=None):return PRINTED_COLOURS.get(getattr(p,'PrintedPartColour','Black'),PRINTED_COLOURS['Black'])
def printed_colour(p=None):
 h=printed_hex(p).lstrip('#');return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
def printed_groove(p=None):
 rgb=printed_colour(p);factor=1.7 if max(rgb)<.25 else .62
 return '#'+''.join(f'{min(255,round(v*255*factor)):02x}' for v in rgb)


def apply_material(view,role,carbon_roles,p=None):
    """Apply physical-part appearance; leave reference electronics untouched."""
    if role in ('MotorEnvelopes','PropellerDiscs','StackEnvelope','CameraEnvelope','VTXEnvelope','BatteryEnvelope'):
        from .reference_options import enabled,SIMPLE
        if enabled(p,role):
            from .detailed_references import apply_reference_material
            apply_reference_material(view,role,p)
        else:
            colour,transparency=SIMPLE[role]
            view.ShapeColor=colour;view.DiffuseColor=[colour];view.Transparency=transparency
        return
    if role not in carbon_roles and role not in ('LiPoPad',)+FLEX_ROLES:return
    carbon=role in carbon_roles
    flexible=printed_colour(p)
    view.ShapeColor=CARBON_COLOR if carbon else flexible
    view.LineColor=(.06,.065,.07) if carbon else (.025,.027,.03)
    view.Transparency=0
    # Modern FreeCAD stores shading in a material list; older versions use a
    # single material property. A single uniform entry also clears per-face tints.
    field='ShapeAppearance' if 'ShapeAppearance' in view.PropertiesList else 'ShapeMaterial' if 'ShapeMaterial' in view.PropertiesList else None
    if field:
        value=getattr(view,field)
        material=value[0] if field=='ShapeAppearance' and value else value
        if material:
            material.DiffuseColor=CARBON_COLOR if carbon else flexible
            material.SpecularColor=(.32,.33,.34) if carbon else (.06,.06,.06)
            material.Shininess=32. if carbon else 2.
            material.Transparency=0.
            setattr(view,field,[material] if field=='ShapeAppearance' else material)
    else:
        if 'SpecularColor' in view.PropertiesList:
            view.SpecularColor=(.32,.33,.34) if carbon else (.06,.06,.06)
        if 'Shininess' in view.PropertiesList:view.Shininess=32. if carbon else 2.

def design_signature(p):
    return tuple('Black' if n=='PrintedPartColour' else getattr(p,n) for n in p.__dataclass_fields__)
