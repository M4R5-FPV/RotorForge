"""Lightweight material colors shared by the native model and editor previews."""
from .flex_options import FLEX_ROLES
CARBON_COLOR=(.18,.19,.20)
CARBON_HEX='#2e3033'
CARBON_EDGE='#111315'
PAD_COLOR=(23/255,25/255,28/255)
PAD_HEX='#17191c'
PAD_GROOVE='#43464a'
# Share propeller colour choices, but use a dedicated neutral black for TPU.
# Old Yellow/Grey finishes are retained for backwards-compatible saved frames.
from .prop_palette import PROP_FINISHES, PROP_FINISH_CHOICES, prop_swatch
LEGACY_PRINTED_COLOURS = {'Yellow': '#f2ce35', 'Grey': '#808890'}
PRINTED_COLOURS = {name: prop_swatch(name) for name in PROP_FINISH_CHOICES}
PRINTED_COLOURS.update(LEGACY_PRINTED_COLOURS)
# Black TPU is neutral and darker than the polycarbonate propeller finish.
PRINTED_BLACK_HEX = "#080808"
PRINTED_COLOURS["Black"] = PRINTED_BLACK_HEX

def printed_hex(p=None):
    return PRINTED_COLOURS.get(getattr(p,'PrintedPartColour','Black'),PRINTED_COLOURS['Black'])

def printed_finish(p=None):
    """RGB and viewport transparency for one unified printed-part finish."""
    name=getattr(p,'PrintedPartColour','Black')
    if name != "Black" and name in PROP_FINISHES:
        return PROP_FINISHES[name]
    h=PRINTED_COLOURS.get(name,PRINTED_COLOURS['Black']).lstrip('#')
    return tuple(int(h[i:i+2],16)/255 for i in (0,2,4)), 0

def printed_colour(p=None):
    return printed_finish(p)[0]

def printed_groove(p=None):
 rgb=printed_colour(p);factor=1.7 if max(rgb)<.25 else .62
 return '#'+''.join(f'{min(255,round(v*255*factor)):02x}' for v in rgb)



# Plain repeatable material, bundled with RotorForge. No file outside the installed
# workbench is required, and the mapping is display-only (not STEP/STL/DXF).
CARBON_TEXTURE_FILENAME = 'carbon_fiber_plain_weave.png'
CARBON_EDGE_TEXTURE_FILENAME = 'carbon_fiber_laminate_edge.png'
CARBON_TEXTURE_FIELDS = frozenset(('CarbonTextureEnabled','CarbonTextureTile','CarbonTextureOpacity'))


def carbon_texture_path():
    from .paths import RESOURCE_DIR
    return str(RESOURCE_DIR / 'textures' / CARBON_TEXTURE_FILENAME)


def carbon_edge_texture_path():
    from .paths import RESOURCE_DIR
    return str(RESOURCE_DIR / 'textures' / CARBON_EDGE_TEXTURE_FILENAME)


def arm_texture_angle(role,p):
    """Rotate the plain weave to follow each manufactured arm, not the body.

    Both 3D shading and 2D inspection use the SAME root-to-motor direction
    from the frame layout. Top, mid, bottom, clamps and keystone stay in the
    XY fuselage weave orientation. No motor-pad cosmetic rotation is involved.
    """
    if p is None or not role or not role.startswith('Arm'):
        return 0.0
    from math import atan2
    from .parameters import arm_layouts
    for arm in arm_layouts(p):
        if role=='Arm'+arm['name']:
            ux,uy=arm['unit']
            return atan2(uy,ux)
    return 0.0


def _clamp_texture_opacity(value):
    import math
    try:value=float(value)
    except (ValueError,TypeError):return 30.0
    return max(0.0,min(100.0,value)) if math.isfinite(value) else 30.0


def opacity_texture_path(opacity=30.,background=CARBON_HEX,source_path=None):
    """Create an *opaque* alpha-composited weave so the carbon stays solid.

    Transparency on a FreeCAD Part/SoMaterial would make the carbon plate
    itself see-through, which is NOT the requested weave opacity. Instead,
    composite the fabric over the flat finish and use a fully opaque texture.
    Result is display-only, stored in an OS temporary cache and keyed by the
    installed texture mtime and the requested blend setting.
    """
    from pathlib import Path
    source=Path(source_path or carbon_texture_path())
    opacity=_clamp_texture_opacity(opacity)
    if opacity>=99.999 or not source.is_file():return str(source)
    from tempfile import gettempdir
    # The appearance pipeline is invoked by FreeCAD GUI code, never in the
    # Python headless geometry/export builders.
    try:
        from PySide import QtGui
    except ImportError:
        try:from PySide2 import QtGui
        except ImportError:from PySide6 import QtGui
    from hashlib import sha256
    digest=sha256((str(source.resolve())+':'+str(source.stat().st_mtime_ns)+':'+str(source.stat().st_size)+':'+str(background)).encode()).hexdigest()[:16]
    output=Path(gettempdir())/'RotorForge_Carbon_Texture_Cache'/f'carbon_{digest}_{int(round(opacity*10)):04d}.png'
    if output.is_file() and output.stat().st_size>0:return str(output)
    original=QtGui.QImage(str(source))
    if original.isNull():return str(source)
    fmt=getattr(QtGui.QImage,'Format_ARGB32',None)
    if fmt is None:fmt=QtGui.QImage.Format.Format_ARGB32
    canvas=QtGui.QImage(original.size(),fmt)
    canvas.fill(QtGui.QColor(background))
    painter=QtGui.QPainter(canvas)
    try:
        painter.setOpacity(opacity/100.)
        painter.drawImage(0,0,original)
    finally:painter.end()
    try:
        output.parent.mkdir(parents=True,exist_ok=True)
        if canvas.save(str(output),'PNG'):return str(output)
    except (OSError,RuntimeError):pass
    return str(source)


from functools import lru_cache


@lru_cache(maxsize=12)
def _preview_carbon_image(qtgui, source, stamp, opacity, background):
    """Cache an in-memory 2D weave tile; do not write per-brush PNGs."""
    original=qtgui.QImage(source)
    if original.isNull():return original
    if opacity>=99.999:return original
    fmt=getattr(qtgui.QImage,'Format_ARGB32',None)
    if fmt is None:fmt=qtgui.QImage.Format.Format_ARGB32
    canvas=qtgui.QImage(original.size(),fmt)
    canvas.fill(qtgui.QColor(background))
    painter=qtgui.QPainter(canvas)
    try:
        painter.setOpacity(opacity/100.)
        painter.drawImage(0,0,original)
    finally:painter.end()
    return canvas


@lru_cache(maxsize=8)
def _preview_carbon_pixmap(qtgui, source, stamp, opacity, background):
    return qtgui.QPixmap.fromImage(_preview_carbon_image(qtgui,source,stamp,opacity,background))


def carbon_brush(p, qtgui, plain=CARBON_HEX, role=None):
    """Tiled 2D brush matching 3D visibility and individual arm direction."""
    if not getattr(p,'CarbonTextureEnabled',False):return qtgui.QColor(plain)
    opacity=_clamp_texture_opacity(getattr(p,'CarbonTextureOpacity',30.))
    if opacity<=0:return qtgui.QColor(plain)
    from pathlib import Path
    source=carbon_texture_path()
    try:stamp=Path(source).stat().st_mtime_ns
    except OSError:return qtgui.QColor(plain)
    # The source is 1024x1024: keep the original visual quality. Avoid
    # repeated disk-save, decode and filesystem hashing during editor draws.
    pix=_preview_carbon_pixmap(qtgui,source,stamp,round(opacity,1),plain)
    if pix.isNull():return qtgui.QColor(plain)
    brush=qtgui.QBrush(pix)
    tile=max(8.0,min(200.0,float(getattr(p,'CarbonTextureTile',64.0))))
    transform=qtgui.QTransform()
    angle=arm_texture_angle(role,p)
    if angle:
        import math
        transform.rotate(math.degrees(angle))
    transform.scale(tile/max(1,pix.width()),tile/max(1,pix.height()))
    brush.setTransform(transform)
    return brush


def _is_texture_node(node):
    try:return str(node.getName()).startswith('RFCarbon')
    except Exception:return False


def _carbon_face_uv_mesh(shape, tile_mm, side_face=False, deflection=0.12, angle=0.0):
    """Explicit UV mesh for the broad laminate faces; no cut-edge projection.

    Native OCC geometry remains untouched. Only planar faces parallel to the
    carbon sheet are textured; narrow CNC-cut sides retain their solid charcoal
    appearance. Coordinates are in the same model space for every plate/arm,
    making the woven pattern continuous across tessellated faces. Arms
    rotate those UV axes to follow their own root-to-motor directions.
    """
    vertices,uv,indices=[],[],[]
    import math
    tile=max(8.0,min(200.0,float(tile_mm)))
    ca,sa=math.cos(angle),math.sin(angle)
    for face in shape.Faces:
        if face.Area<0.01 or type(face.Surface).__name__!='Plane':
            continue
        normal=face.normalAt(0.0,0.0)
        if side_face:
            if abs(normal.y)<0.985:continue
        else:
            if abs(normal.z)<0.985:continue
        pts,triangles=face.tessellate(deflection)
        if not pts or not triangles:continue
        # The input BRep is in global RotorForge design coordinates. Only
        # vertical side-plates use XZ; all main laminate sheets use XY.
        start=len(vertices)
        for v in pts:
            vertices.append((float(v.x),float(v.y),float(v.z)))
            u,vv=((v.x,v.z) if side_face else (v.x,v.y))
            # Project into each arm's own root-to-motor reference frame.
            # Other carbon sheets use ca=1,sa=0 for fuselage alignment.
            u,vv=ca*u+sa*vv,-sa*u+ca*vv
            uv.append((float(u)/tile,float(vv)/tile))
        for tri in triangles:
            if len(tri)!=3:continue
            a,b,c=(int(v) for v in tri)
            if a==b or b==c or a==c:continue
            indices.extend((start+a,start+b,start+c,-1))
    return vertices,uv,indices



# A laminated carbon part has two visually distinct manufactured surfaces:
# woven cloth on the sheet faces, and closely spaced ply edges at CNC-cut walls.
# This repeat describes eight 0.25 mm plies without depending on the main weave
# texture scale; 2 mm / eight stripes makes the detail visible on 2–5 mm sheets.
CARBON_EDGE_REPEAT_MM = 2.0
CARBON_EDGE_LENGTH_REPEAT_MM = 18.0


def _carbon_cut_edge_uv_mesh(shape, side_face=False, deflection=0.10):
    """UV for cut edges, including filleted and circular edges, never broad faces.

    Lamination lines are parallel to the laminate broad surface and stacked
    along sheet thickness. Horizontal plates are layered along global Z;
    vertical camera-side plates are layered along global Y. Per-triangle
    classification includes curved OCC faces and rejects the planar broad
    faces. All UV coordinates are computed in physical 3D space, so the
    perimeter cannot stretch a single sampled texture pixel into a smear.
    """
    import math
    vertices,uv,indices=[],[],[]
    axis=1 if side_face else 2
    for face in shape.Faces:
        if face.Area < 0.005:continue
        # Avoid a second (potentially expensive) tessellation of every broad
        # face. Flat sheet faces have no extent through the ply stack.
        box=getattr(face,'BoundBox',None)
        if box is not None:
            span=getattr(box,'YLength' if side_face else 'ZLength',None)
            if span is not None and span < 0.001:continue
        pts,triangles=face.tessellate(deflection)
        if not pts or not triangles:continue
        for triangle in triangles:
            if len(triangle)!=3:continue
            a,b,c=(int(i) for i in triangle)
            if min(a,b,c)<0 or max(a,b,c)>=len(pts) or len({a,b,c})!=3:continue
            p0,p1,p2=(pts[a],pts[b],pts[c])
            va=(p1.x-p0.x,p1.y-p0.y,p1.z-p0.z)
            vb=(p2.x-p0.x,p2.y-p0.y,p2.z-p0.z)
            nx=va[1]*vb[2]-va[2]*vb[1]
            ny=va[2]*vb[0]-va[0]*vb[2]
            nz=va[0]*vb[1]-va[1]*vb[0]
            area2=math.sqrt(nx*nx+ny*ny+nz*nz)
            if area2<1.e-8:continue
            # Broad carbon faces (including triangulation across holes) are
            # already drawn with the plain weave. Edge faces may be round.
            thickness_normal=(ny if side_face else nz)/area2
            if abs(thickness_normal)>.985:continue
            coords=[(float(v.x),float(v.y),float(v.z)) for v in (p0,p1,p2)]
            for x,y,z in coords:
                vertices.append((x,y,z))
                if side_face:
                    along=x+.37*z;thickness=y
                else:
                    along=x+.37*y;thickness=z
                uv.append((along/CARBON_EDGE_LENGTH_REPEAT_MM,
                           thickness/CARBON_EDGE_REPEAT_MM))
            i=len(vertices)-3
            indices.extend((i,i+1,i+2,-1))
    return vertices,uv,indices


def _add_carbon_overlay(root,coin,name,asset,vertices,uv,indices):
    """Add an unpickable visual coating on the existing native Part geometry."""
    if not indices:return False
    layer=coin.SoSeparator();layer.setName(name)
    pick=coin.SoPickStyle();pick.style.setValue(coin.SoPickStyle.UNPICKABLE)
    layer.addChild(pick)
    offset=coin.SoPolygonOffset();offset.factor.setValue(-1.0);offset.units.setValue(-1.0)
    offset.styles.setValue(coin.SoPolygonOffset.FILLED)
    layer.addChild(offset)
    material=coin.SoMaterial();material.diffuseColor.setValue(.95,.95,.95)
    material.specularColor.setValue(.15,.15,.15)
    material.shininess.setValue(.2)
    layer.addChild(material)
    texture=coin.SoTexture2();texture.setName(name+'Texture')
    texture.filename.setValue(asset)
    texture.wrapS.setValue(coin.SoTexture2.REPEAT)
    texture.wrapT.setValue(coin.SoTexture2.REPEAT)
    texture.model.setValue(coin.SoTexture2.MODULATE)
    layer.addChild(texture)
    coord=coin.SoCoordinate3();coord.point.setValues(0,len(vertices),vertices)
    texcoord=coin.SoTextureCoordinate2();texcoord.point.setValues(0,len(uv),uv)
    layer.addChild(coord);layer.addChild(texcoord)
    faceset=coin.SoIndexedFaceSet();faceset.coordIndex.setValues(0,len(indices),indices)
    layer.addChild(faceset)
    root.addChild(layer)
    return True


def _carbon_mesh_state(shape,tile_mm,side_face,angle):
    """Cheap display-only identity; never used for manufacturing or CAD reuse."""
    import hashlib
    box=shape.BoundBox
    key=(shape.hashCode(),len(shape.Faces),round(shape.Volume,7),
         tuple(round(v,7) for v in (box.XMin,box.XMax,box.YMin,box.YMax,box.ZMin,box.ZMax)),
         round(float(tile_mm),7),bool(side_face),round(float(angle),11))
    return 'RFCarbonGeometry_'+hashlib.blake2s(repr(key).encode(),digest_size=12).hexdigest()


def _carbon_scene_layers(root):
    layers={}
    for i in range(root.getNumChildren()):
        node=root.getChild(i)
        try:name=str(node.getName())
        except Exception:continue
        if name.startswith('RFCarbon'):layers[name]=node
    return layers


def _refresh_carbon_texture_asset(layer,texture_name,asset):
    """Change the image without resampling thousands of OCC tessellation faces."""
    if layer is None:return
    for i in range(layer.getNumChildren()):
        node=layer.getChild(i)
        if str(node.getName())==texture_name:
            if str(node.filename.getValue())!=str(asset):
                node.filename.setValue(str(asset))
            return


# The native Part display-mode groups are FreeCAD-owned. Never insert, remove
# or share overlay children inside them. A single private switch at the root
# gates the original independent overlay without touching native mesh state.
_CARBON_OVERLAY_ROOT = 'RFCarbonOverlayRoot'


def _carbon_gate(root):
    """Find this part's independent texture switch in the Coin scenegraph."""
    for i in range(root.getNumChildren()):
        node=root.getChild(i)
        if (str(node.getName())==_CARBON_OVERLAY_ROOT and
                node.getNumChildren()==1):
            return node.getChild(0)
    return None


def _set_carbon_gate(gate,visible):
    choice=0 if visible else -1  # -1 = SoSwitch.SO_SWITCH_NONE
    if gate.whichChild.getValue()!=choice:
        gate.whichChild.setValue(choice)
class CarbonTextureViewProvider:
    """Tie display-only carbon overlays to the native FreeCAD part visibility.

    The overlay is a private child of the view's scene root and therefore
    needs an explicit SoSwitch update whenever a user hides/shows the Part in
    the tree. A ViewProvider's onChanged callback receives these GUI property
    changes; an App/Gui document observer does not reliably receive them.
    """
    def __init__(self, view=None):
        if view is not None:
            view.Proxy = self

    def onChanged(self, view, prop):
        if prop == 'Visibility':
            sync_carbon_visibility(view)

    def dumps(self):
        return None

    def loads(self, state):
        pass

    __getstate__ = dumps
    __setstate__ = loads


def sync_carbon_visibility(view):
    """Update only RotorForge's switch; never change the native Part display."""
    from .coin_support import scene_root
    root=scene_root(view)
    if root is None:return
    gate=_carbon_gate(root)
    if gate is None or gate.getNumChildren()!=1:return
    layer=gate.getChild(0)
    _set_carbon_gate(gate, bool(view.Visibility) and
                     str(layer.getName())=='RFCarbonEnabled')


def _ensure_carbon_view_proxy(view):
    """Bind once, including on restored v1.0.8 frames and appearance edits."""
    try:
        proxy=getattr(view,'Proxy',None)
        if isinstance(proxy,CarbonTextureViewProvider):
            return True
        CarbonTextureViewProvider(view)
        return isinstance(getattr(view,'Proxy',None),CarbonTextureViewProvider)
    except (AttributeError, RuntimeError, TypeError):
        return False


def _carbon_overlay_parent(view,root,coin,create):
    # Remove only our old root-level nodes (from pre-1.0.11 sessions).
    # The 1.0.11 mode-group overlays were transient; a full restart clears them.
    for i in range(root.getNumChildren()-1,-1,-1):
        node=root.getChild(i)
        if _is_texture_node(node) and str(node.getName())!=_CARBON_OVERLAY_ROOT:
            root.removeChild(i)
    gate=_carbon_gate(root)
    if create and not _ensure_carbon_view_proxy(view):return None
    if gate is None:
        if not create:return None
        wrapper=coin.SoSeparator();wrapper.setName(_CARBON_OVERLAY_ROOT)
        gate=coin.SoSwitch();gate.setName('RFCarbonOverlaySwitch')
        _set_carbon_gate(gate,False)
        layer=coin.SoSeparator();layer.setName('RFCarbonDisabled')
        gate.addChild(layer);wrapper.addChild(gate);root.addChild(wrapper)
    layer=gate.getChild(0)
    layer.setName('RFCarbonDisabled')
    _set_carbon_gate(gate,False)  # finish building while it is not traversed
    return layer if create else None


def _show_carbon_overlay(view,root):
    gate=_carbon_gate(root)
    if gate is not None:
        gate.getChild(0).setName('RFCarbonEnabled')
        sync_carbon_visibility(view)


def apply_carbon_texture(view,enabled=False,tile_mm=64.0,side_face=False,opacity=30.,angle=0.0):
    """Plain weave and cut-edge layers, reusing their scene meshes when possible.

    OCC tessellation is expensive. Identical views keep their existing overlay
    nodes; opacity-only changes swap image files rather than rebuilding meshes.
    A different geometry, scale or weave angle always rebuilds the overlay.
    """
    from .coin_support import initialize_coin, scene_root
    coin=initialize_coin()
    if coin is None:return False
    root=scene_root(view)
    if root is None:return False
    owner=getattr(view,'Object',None)
    shape=getattr(owner,'Shape',None)
    active=enabled and _clamp_texture_opacity(opacity)>0 and shape is not None and not shape.isNull()
    parent=_carbon_overlay_parent(view,root,coin,active)
    if not active:return not enabled or _clamp_texture_opacity(opacity)<=0
    # Do not fall back to a detached overlay that cannot follow visibility.
    if parent is None:return False
    native_root=root
    root=parent
    layers=_carbon_scene_layers(root)
    from pathlib import Path
    broad_asset=opacity_texture_path(opacity)
    edge_asset=opacity_texture_path(opacity,source_path=carbon_edge_texture_path())
    if not Path(broad_asset).is_file() or not Path(edge_asset).is_file():return False
    state=_carbon_mesh_state(shape,tile_mm,side_face,angle)
    if state in layers and ('RFCarbonSurfaceOverlay' in layers or 'RFCarbonEdgeOverlay' in layers):
        _refresh_carbon_texture_asset(layers.get('RFCarbonSurfaceOverlay'),
                                      'RFCarbonSurfaceOverlayTexture',broad_asset)
        _refresh_carbon_texture_asset(layers.get('RFCarbonEdgeOverlay'),
                                      'RFCarbonEdgeOverlayTexture',edge_asset)
        _show_carbon_overlay(view,native_root)
        return True
    # Rebuild only if a geometry or mapping parameter really changed.
    for i in range(root.getNumChildren()-1,-1,-1):
        if _is_texture_node(root.getChild(i)):root.removeChild(i)
    broad=_carbon_face_uv_mesh(shape,tile_mm,side_face,angle=angle)
    cut=_carbon_cut_edge_uv_mesh(shape,side_face=side_face)
    a=_add_carbon_overlay(root,coin,'RFCarbonSurfaceOverlay',broad_asset,*broad)
    b=_add_carbon_overlay(root,coin,'RFCarbonEdgeOverlay',edge_asset,*cut)
    if a or b:
        marker=coin.SoSeparator();marker.setName(state);root.addChild(marker)
        _show_carbon_overlay(view,native_root)
    else:root.setName('RFCarbonDisabled')
    return a or b


def set_face_colours(view, colours, transparency=None):
    """Colour faces using the API actually exposed by this FreeCAD view provider.

    FreeCAD Part view providers differ: some expose the old DiffuseColor
    array, while modern GeometryObject providers have ShapeAppearance or
    ShapeMaterial and *no* DiffuseColor attribute.  Never assign a dynamic
    property that does not exist: it raises AttributeError and can abort a
    perfectly valid frame build.
    """
    palette=[tuple(float(value) for value in colour[:3]) for colour in colours]
    if not palette:
        return False
    if hasattr(view,'DiffuseColor'):
        try:
            view.DiffuseColor=palette
            return True
        except (AttributeError,TypeError,ValueError,RuntimeError):
            pass

    properties=getattr(view,'PropertiesList',())
    field=('ShapeAppearance' if 'ShapeAppearance' in properties else
           'ShapeMaterial' if 'ShapeMaterial' in properties else None)
    if field is None:
        # ShapeColor is set by callers. A view provider with no material
        # arrays can still display a correctly coloured solid.
        return False
    try:
        source=getattr(view,field)
        template=(source[0] if source else None) if field=='ShapeAppearance' else source
        from copy import copy
        materials=[]
        for rgb in (palette if field=='ShapeAppearance' else palette[:1]):
            try:
                material=copy(template) if template is not None else None
                if material is None or material is template:
                    raise TypeError('material could not be independently copied')
            except (TypeError,ValueError,AttributeError,RuntimeError):
                import FreeCAD as App
                material=App.Material()
                if template is not None:
                    for attribute in ('AmbientColor','EmissiveColor','SpecularColor','Shininess'):
                        try:setattr(material,attribute,getattr(template,attribute))
                        except (AttributeError,TypeError,ValueError):pass
            material.DiffuseColor=rgb
            if transparency is not None:
                material.Transparency=max(0.,min(1.,float(transparency)/100.))
            materials.append(material)
        setattr(view,field,materials if field=='ShapeAppearance' else materials[0])
        return True
    except (AttributeError,TypeError,ValueError,RuntimeError):
        # Cosmetic colouring must never invalidate a sound CAD assembly.
        return False


def apply_material(view,role,carbon_roles,p=None):
    if role in ('VTXAntennaReference','ELRSTReference'):
        from .antenna_reference_models import antenna_reference,reference_enabled,VTX_COLOUR,ELRS_COLOUR
        base=VTX_COLOUR if role=='VTXAntennaReference' else ELRS_COLOUR
        colours=antenna_reference(p,role)[1] if p is not None and reference_enabled(p,role) else ()
        view.ShapeColor=base;view.LineColor=(.035,.042,.050)
        set_face_colours(view,colours if colours else (base,),0)
        view.Transparency=0
        return
    """Apply physical-part appearance; leave reference electronics untouched."""
    if role in ('MotorEnvelopes','PropellerDiscs','StackEnvelope','CameraEnvelope','VTXEnvelope','BatteryEnvelope'):
        from .reference_options import enabled,SIMPLE
        if enabled(p,role):
            from .detailed_references import apply_reference_material
            apply_reference_material(view,role,p)
        else:
            colour,transparency=SIMPLE[role]
            view.ShapeColor=colour;set_face_colours(view,(colour,),transparency);view.Transparency=transparency
            reset_face_materials(view,(colour,),transparency)
        return
    if p is not None and role in ('CameraMountLeft','CameraMountRight') and p.CameraCageStyle!='Carbon side plates':
        colour,alpha=printed_finish(p) if p.CameraCageStyle=='TPU cage' else ((.68,.70,.73),0)
        view.ShapeColor=colour;set_face_colours(view,(colour,),alpha)
        # Match the dark edges of other printed parts, with a small lift
        # for the cage's rounded surfaces. Keep the metal holder untouched.
        view.LineColor=(.035,.037,.040) if p.CameraCageStyle=='TPU cage' else (.08,.09,.10)
        reset_face_materials(view,(colour,),alpha)
        # A previous carbon camera side panel can become a TPU cage. Drop the
        # old weave shader before returning to the printed-material finish.
        apply_carbon_texture(view,False)
        return
    if role not in carbon_roles and role not in ('LiPoPad',)+FLEX_ROLES:
        apply_carbon_texture(view,False)
        return
    carbon=role in carbon_roles
    flexible, flex_transparency=printed_finish(p)
    textured=carbon and bool(getattr(p,"CarbonTextureEnabled",False))
    shade=CARBON_COLOR  # Cut carbon edges stay dark even when faces are textured
    view.ShapeColor=shade if carbon else flexible
    view.LineColor=(.06,.065,.07) if carbon else (.025,.027,.03)
    transparency=0 if carbon else flex_transparency
    set_face_colours(view,(shade if carbon else flexible,),transparency)
    view.Transparency=transparency
    # Modern FreeCAD stores shading in a material list; older versions use a
    # single material property. A single uniform entry also clears per-face tints.
    field='ShapeAppearance' if 'ShapeAppearance' in view.PropertiesList else 'ShapeMaterial' if 'ShapeMaterial' in view.PropertiesList else None
    if field:
        value=getattr(view,field)
        material=value[0] if field=='ShapeAppearance' and value else value
        if material:
            material.DiffuseColor=shade if carbon else flexible
            material.SpecularColor=(.32,.33,.34) if carbon else (.06,.06,.06)
            material.Shininess=32. if carbon else 2.
            material.Transparency=transparency/100.
            setattr(view,field,[material] if field=='ShapeAppearance' else material)
            # Some FreeCAD releases reset the object's transparency on assigning
            # the shape appearance, so restore the public 0..100 viewport value.
            view.Transparency=transparency
    else:
        if 'SpecularColor' in view.PropertiesList:
            view.SpecularColor=(.32,.33,.34) if carbon else (.06,.06,.06)
        if 'Shininess' in view.PropertiesList:view.Shininess=32. if carbon else 2.
    if carbon:
        try:
            apply_carbon_texture(view,textured,getattr(p,"CarbonTextureTile",64.0),
                                 role in ("CameraMountLeft","CameraMountRight"),
                                 getattr(p,"CarbonTextureOpacity",30.),arm_texture_angle(role,p))
        except Exception as e:
            # Legacy/non-GUI FreeCAD builds may not provide scenegraph texture nodes.
            try:
                import FreeCAD as App
                App.Console.PrintWarning("RotorForge carbon texture: " + str(e) + "\n")
            except Exception:pass

def design_signature(p):
    return tuple(False if n=='CarbonTextureEnabled' else 64.0 if n=='CarbonTextureTile' else 30.0 if n=='CarbonTextureOpacity' else 'Black' if n=='PrintedPartColour' else 'Matte black' if n=='VTXAntennaHeadColour' else 'Smoke grey' if n=='PropReferenceColour' else 'Black' if n=='MotorReferenceColour' else getattr(p,n) for n in p.__dataclass_fields__)


def reset_face_materials(view,colours,transparency):
    """Replace obsolete per-face tints via the supported view material API."""
    set_face_colours(view,colours,transparency)
    if hasattr(view,'Transparency'):
        view.Transparency=transparency
