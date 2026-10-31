"""Persistent FreeCAD parameters and dependent per-part FeaturePython proxies."""
from dataclasses import fields
from .paths import icon_path
import FreeCAD as App
import Part

from . import __version__
from .parameters import Parameters, ENUMERATIONS, BOOLEANS, STRINGS, VENT_ROW_COUNTS, ARM_LOCK_FIELDS, require_valid, prop_gap, three_plate
from .geometry import ALL_ROLES, CARBON_ROLES, ARM_LOCK_ROLES, LEGACY_ARM_ROLES, carbon_roles, normalise_role, build_shapes, invalidate_failed_build
from .fpv import FPV_FIELDS, CAMERA_ROLES, TAB_OFFSET_FIELDS
from .arm_roots import ROOT_BOLT_COORDINATES, LEGACY_ROOT_BOLT_COORDINATES

ICON = icon_path()
from .parameters import RETIRED_PARAMETERS,STACK_PATTERNS,stack_label

FLOATS = {"BottomNoseTipWidth","FlexDensity","PlateEndWidth","ArmProfileAmount","LiPoPadOutlineWidthScale","LiPoPadOutlineLengthScale","MotorMass","PropMass","FCMass","ESCMass","VTXMass","CameraMass","OtherMass","ScrewMassScale","LengthToWidth", "FrontSpread", "CarbonDensity", "LiPoPadDensity", "StandoffDensity", "BatteryMass"}
SIGNED_LENGTHS = {'StrapSingleY','StackUSBOffsetY','FlexGuardStrapY1','FlexGuardStrapY2','FlexGuardVentBoundaryOffset','FlexGuardVTXY','FlexGuardVTXZ','FlexGuardVTXVentZOffset','FlexGuardFCVentZOffset',"FlexGuardWireFrontY","FlexGuardWireRearY","FlexGuardUSBY","StackOffsetY", "StandoffPair3Y", "StandoffPair4Y", "VTXOffsetY", 'CentreSectionY','BatteryX','BatteryY'} | ROOT_BOLT_COORDINATES | set(TAB_OFFSET_FIELDS)
GEOMETRY_FIELDS = {"Layout", "PlateDesign", "Wheelbase", "LengthToWidth", "FrontSpread", "RearArmExtension", "PropDiameter", "RequiredPropGap"}
ARM_FIELDS = {"ArmBeamShape","ArmProfileAmount","ArmThickness", "ArmWidth", "ArmRootY", "RootInset", "RootExtension", "RootBoltSpacing", "RootHoleDiameter"}|ARM_LOCK_FIELDS
MOTOR_FIELDS = {"MotorPadNeckLength","MotorPadBlendRadius","MotorPadRelief","MotorPadReliefWidth","MotorPadReliefLength","MotorPadDiameter", "MotorSpacingX", "MotorSpacingY", "MotorHoleDiameter", "MotorCenterDiameter", 'MotorPadShape', 'MotorPadCornerRadius', 'MotorTipLength','MotorTipSlotEnabled','MotorTipSlotWidth','MotorTipSlotLength'}


def property_group(name):
    from .nut_seats import FIELDS as NUT_FIELDS
    if name in NUT_FIELDS:return "16 Nut retention"
    if name=="PrintedPartColour":return "15 Appearance"
    if name.startswith("Flex"):return "14 Flexible parts"
    from .equipment_mass import MASS_FIELDS
    if name in MASS_FIELDS or name=="EstimateComponents":return "13 Equipment estimates"
    if name=="KeystoneShape":return "03 Arms"
    if name.startswith(("Battery","LiPoPad")):return "12 Battery and pad"
    if name in ("StandoffDensity","ShowFrameCG"):return "08 Checks and references"
    if name.startswith(("MotorReference","PropReference")) or name in ("MotorHoleLayout","MotorBoltCircle","MotorHoleRotation","MotorPadRotation","MotorPadRotationPivot"):return "04 Motor mounts"
    if name in STRINGS:
        return '11 Airflow cutouts'
    if name in FPV_FIELDS:
        return "10 FPV camera and VTX"
    if name in GEOMETRY_FIELDS:
        return "01 Frame geometry"
    if name in ARM_FIELDS:
        return "03 Arms"
    if name in MOTOR_FIELDS:
        return "04 Motor mounts"
    if name.startswith("Stack"):
        return "05 Electronics"
    if name.startswith("Standoff"):
        return "06 Standoffs"
    if name.startswith("Strap"):
        return "07 Battery straps"
    if name in ("MinimumWeb", "CarbonDensity", "ShowReferences"):
        return "08 Checks and references"
    return "02 Plates"


def read_parameters(obj):
    properties=set(obj.PropertiesList)
    if 'FrameStyle' in properties and str(obj.FrameStyle)!='Plate frame':
        raise ValueError('This saved construction is no longer supported. Use a two- or three-plate design.')
    data = {}
    for f in fields(Parameters):
        if f.name not in properties:
            continue
        value = getattr(obj, f.name)
        if f.name=='StackSpacing' and obj.getTypeIdOfProperty(f.name)=='App::PropertyEnumeration':
            value=str(value)
        elif f.name in ENUMERATIONS or f.name in STRINGS:
            value = str(value)
        elif f.name not in BOOLEANS:
            value = float(value.Value if hasattr(value, "Value") else value)
        data[f.name] = value
    for name in ('CameraCutoutWidth','CameraCutoutDepth','CameraCutoutClearance'):
        if name in properties:
            value=getattr(obj,name);data[name]=float(value.Value if hasattr(value,'Value') else value)
    if not ROOT_BOLT_COORDINATES <= properties:
        for name in LEGACY_ROOT_BOLT_COORDINATES:
            if name in properties:
                value=getattr(obj,name)
                data[name]=float(value.Value if hasattr(value,'Value') else value)
    return Parameters.from_dict(data)


def set_parameters(obj, p):
    require_valid(p)
    if isinstance(obj.Proxy,ParameterProxy):obj.Proxy._restored_signature=None
    ensure_parameter_properties(obj, p)
    for f in fields(p):
        value=stack_label(p.StackSpacing) if f.name=='StackSpacing' else int(round(getattr(p,f.name))) if f.name in VENT_ROW_COUNTS else getattr(p,f.name)
        old=getattr(obj,f.name);old=old.Value if hasattr(old,'Value') else old
        if old!=value:setattr(obj,f.name,value)


def ensure_parameter_properties(obj, defaults=None):
    """Add new fields without replacing dimensions in existing 0.1 documents."""
    defaults = defaults or read_parameters(obj)
    for name in list(obj.PropertiesList):
        if name in RETIRED_PARAMETERS:obj.removeProperty(name)
    if 'CameraPositionMode' not in obj.PropertiesList and 'CameraMountY' in obj.PropertiesList:
        # Convert the older midpoint-based two-screw camera location once.
        obj.CameraMountY=defaults.CameraMountY
        obj.CameraPivotHeight=defaults.CameraPivotHeight
    for f in fields(defaults):
        if f.name=='StackSpacing' and f.name in obj.PropertiesList and obj.getTypeIdOfProperty(f.name)!='App::PropertyEnumeration':obj.removeProperty(f.name)
        if f.name in VENT_ROW_COUNTS and f.name in obj.PropertiesList and obj.getTypeIdOfProperty(f.name)!='App::PropertyIntegerConstraint':obj.removeProperty(f.name)
        if f.name in obj.PropertiesList:
            if f.name.startswith('KeystoneRetainer') or f.name in ('MotorSpacingX','MotorSpacingY','LiPoPadOutlineLengthScale'):obj.setEditorMode(f.name,2)
            if f.name in ENUMERATIONS and obj.getEnumerationsOfProperty(f.name)!=list(ENUMERATIONS[f.name]):
                setattr(obj,f.name,list(ENUMERATIONS[f.name]))
                setattr(obj,f.name,getattr(defaults,f.name))
                if f.name=='MotorHoleLayout':
                    for name in ('MotorBoltCircle','MotorHoleRotation'):
                        if name in obj.PropertiesList:setattr(obj,name,getattr(defaults,name))
            if f.name in SIGNED_LENGTHS and obj.getTypeIdOfProperty(f.name) == "App::PropertyLength":
                # Length clamps negative values to zero; Distance is signed.
                obj.removeProperty(f.name)
            else:
                if f.name=='StackSpacing':
                    obj.StackSpacing=[text for text,value in STACK_PATTERNS];obj.StackSpacing=stack_label(defaults.StackSpacing)
                continue
        kind = ("App::PropertyIntegerConstraint" if f.name in VENT_ROW_COUNTS else
                "App::PropertyEnumeration" if f.name in ENUMERATIONS or f.name=='StackSpacing' else
                "App::PropertyBool" if f.name in BOOLEANS else
                "App::PropertyString" if f.name in STRINGS else
                "App::PropertyAngle" if f.name in ("CameraTilt",'CameraTiltMin','CameraTiltMax','MotorHoleRotation','MotorPadRotation','BatteryRotation') else
                "App::PropertyDistance" if f.name in SIGNED_LENGTHS else
                "App::PropertyFloat" if f.name in FLOATS else "App::PropertyLength")
        obj.addProperty(kind, f.name, property_group(f.name), FLEX_OPTIONS[f.name][2] if f.name in FLEX_OPTIONS else f.name)
        if f.name=='StackSpacing':setattr(obj,f.name,[text for text,value in STACK_PATTERNS])
        elif f.name in ENUMERATIONS:setattr(obj,f.name,list(ENUMERATIONS[f.name]))
        setattr(obj,f.name,(int(round(getattr(defaults,f.name))),1,6,1) if f.name in VENT_ROW_COUNTS else stack_label(defaults.StackSpacing) if f.name=='StackSpacing' else getattr(defaults,f.name))
        if f.name.startswith('KeystoneRetainer') or f.name in ('MotorSpacingX','MotorSpacingY','LiPoPadOutlineLengthScale'):obj.setEditorMode(f.name,2)
    if 'VTXNutMount' in obj.PropertiesList:obj.removeProperty('VTXNutMount')
    for name in LEGACY_ROOT_BOLT_COORDINATES:
        if name in obj.PropertiesList:obj.removeProperty(name)


def apply_document_appearance(settings,p):
    """View-only update: never assign a Shape or invoke a CAD builder."""
    if App.GuiUp:
        for role,obj in component_objects(settings).items():apply_material(obj.ViewObject,role,CARBON_ROLES,p)
    for kind,name,value in (('App::PropertyFloat','LastBuildSeconds',0.),('App::PropertyStringList','RebuiltComponents',[]),('App::PropertyStringList','ReusedComponents',list(component_objects(settings)))):
        if name not in settings.PropertiesList:
            settings.addProperty(kind,name,'09 Results','Incremental geometry build diagnostics',8);settings.setEditorMode(name,1)
        if getattr(settings,name)!=value:setattr(settings,name,value)

class ParameterProxy:
    def __init__(self, obj, p):
        obj.Proxy = self
        set_parameters(obj, p)
        for kind, name, desc in (("App::PropertyString", "GeneratorVersion", "RotorForge plugin version"),
                                  ("App::PropertyString", "Status", "Validation status"),
                                  ("App::PropertyStringList", "Warnings", "Layout checks; these are not strength calculations"),
                                  ("App::PropertyFloat", "CarbonMassGrams", "Estimated plate and arm mass, excludes hardware"),
                                  ("App::PropertyLength", "MinimumPropGap", "Closest propeller edge-to-edge distance")):
            obj.addProperty(kind, name, "09 Results", desc, 8)  # Prop_Output
            obj.setEditorMode(name, 1)
        obj.GeneratorVersion = __version__

    def execute(self, obj):
        try:
            p = read_parameters(obj)
            previous=getattr(self,'_restored_signature',None) or getattr(self,'_last_full_signature',None)
            if previous and previous!=p.signature():
                from .appearance import design_signature
                if design_signature(Parameters(*previous))==design_signature(p):
                    apply_document_appearance(obj,p);self._restored_signature=p.signature();self._last_full_signature=p.signature();return
            if getattr(self,'_restored_signature',None)==p.signature():return
            self._restored_signature=None
            warnings = require_valid(p)
            from .geometry import prime_document_cache,build_report
            prime_document_cache(obj)
            from .geometry import build_for_update
            pending=getattr(self,'_pending_report',None)
            shapes=build_shapes(p) if pending is not None else build_for_update(p)
            report=pending if pending is not None else build_report(p)
            self._pending_report=None
            for kind,name in (('App::PropertyFloat','LastBuildSeconds'),('App::PropertyStringList','RebuiltComponents'),('App::PropertyStringList','ReusedComponents')):
                if name not in obj.PropertiesList:obj.addProperty(kind,name,'09 Results','Incremental geometry build diagnostics',8);obj.setEditorMode(name,1)
            obj.LastBuildSeconds=report.get('seconds',0.)
            obj.RebuiltComponents=report.get('rebuilt',[])
            obj.ReusedComponents=report.get('reused',[])
            from .mass_properties import mass_properties
            metrics=mass_properties(p,shapes)
            for kind,name,desc in [('App::PropertyFloat','FrameMassGrams','Estimated carbon + standoffs + LiPo pad + flexible parts; excludes screws and electronics'),('App::PropertyVector','FrameCG','Estimated bare frame centre of gravity in frame coordinates'),('App::PropertyFloat','FramePlusBatteryMassGrams','Frame estimate plus reference battery only'),('App::PropertyVector','FramePlusBatteryCG','Frame plus reference battery only; excludes electronics and motors')]:
                if name not in obj.PropertiesList:
                    obj.addProperty(kind,name,'09 Results',desc,8);obj.setEditorMode(name,1)
            for key in ('Equipped','Loaded'):
                for kind,suffix in [('App::PropertyFloat','MassGrams'),('App::PropertyVector','CG')]:
                    name=key+suffix
                    if name not in obj.PropertiesList:obj.addProperty(kind,name,'09 Results','Nominal equipment estimate',8);obj.setEditorMode(name,1)
                setattr(obj,key+'MassGrams',metrics.get(key.lower()+'_mass_g',0.))
                setattr(obj,key+'CG',App.Vector(*metrics.get(key.lower()+'_cg_mm',(0.,0.,0.))))
            obj.FrameMassGrams=metrics['frame_mass_g'];obj.FrameCG=App.Vector(*metrics['frame_cg_mm'])
            obj.FramePlusBatteryMassGrams=metrics.get('frame_plus_battery_mass_g',0.)
            obj.FramePlusBatteryCG=App.Vector(*metrics.get('frame_plus_battery_cg_mm',(0.,0.,0.)))
            self._last_full_signature=p.signature()
            obj.GeneratorVersion = __version__
            obj.CarbonMassGrams = sum(shapes[role].Volume for role in carbon_roles(p)) * p.CarbonDensity / 1000
            obj.MinimumPropGap = prop_gap(p)
            obj.Warnings = warnings
            obj.Status = "Valid" if not warnings else "Valid — review warnings"
            # References use dimensions only, so synchronize without a nested
            # document recompute. A reference error must not invalidate carbon.
            from .hardware_refs import sync_refs,invalidate_refs
            try:sync_refs(obj)
            except Exception as reference_error:
                invalidate_refs(obj)
                App.Console.PrintWarning('RotorForge hardware references: '+str(reference_error)+'\n')

        except Exception as exc:
            from .hardware_refs import invalidate_refs
            invalidate_refs(obj)
            obj.Status = "Invalid: " + str(exc).replace("\n", "; ")
            obj.Warnings = [str(exc)]
            obj.CarbonMassGrams = 0
            obj.MinimumPropGap = 0
            for name in ('FrameMassGrams','FramePlusBatteryMassGrams','EquippedMassGrams','LoadedMassGrams'):
                if name in obj.PropertiesList:setattr(obj,name,0.)
            for name in ('FrameCG','FramePlusBatteryCG','EquippedCG','LoadedCG'):
                if name in obj.PropertiesList:setattr(obj,name,App.Vector())
            App.Console.PrintError("RotorForge: " + str(exc) + "\n")

    def onDocumentRestored(self, obj):
        # Reading a saved frame must not migrate/touch its properties and queue
        # a full rebuild. Keep its persisted BReps until an actual parameter
        # change or the editor's explicit Update action requests regeneration.
        try:self._restored_signature=read_parameters(obj).signature()
        except Exception:self._restored_signature=None

    def dumps(self):
        return None

    def loads(self, state):
        pass

    # Older FreeCAD releases use pickle rather than JSON proxy persistence.
    __getstate__ = dumps
    __setstate__ = loads


class PartProxy:
    def __init__(self, obj, settings, role):
        obj.addProperty("App::PropertyLink", "Parameters", "RotorForge", "Shared frame parameters").Parameters = settings
        obj.addProperty("App::PropertyString", "FrameRole", "RotorForge", "Generated component role").FrameRole = role
        obj.setEditorMode("Parameters", 1)
        obj.setEditorMode("FrameRole", 1)
        obj.Proxy = self

    def execute(self, obj):
        try:
            p = read_parameters(obj.Parameters)
            if getattr(obj.Parameters.Proxy,'_restored_signature',None)==p.signature():return
            role = normalise_role(obj.FrameRole)
            from .geometry import build_shape
            shape = build_shape(p,role)
            placement = App.Placement(shape.Placement)
            import hashlib,json
            from .dependency_cache import shape_token
            from .geometry import component_manifest,component_payload
            manifest=component_manifest(role,p);token=json.loads(manifest)['token'] if manifest else shape_token(shape)
            current=hashlib.sha256(obj.Shape.exportBrepToString().encode()).hexdigest()
            unchanged=False
            if all(n in obj.PropertiesList for n in ('ComponentCache','ComponentDocumentDigest')):
                try:unchanged=json.loads(str(obj.ComponentCache)).get('token')==token and (str(obj.ComponentDocumentDigest)==current or getattr(self,'_verified_document_digest',None)==current)
                except (ValueError,TypeError,AttributeError):pass
            if not unchanged:
                # Prepare display triangulation on the GUI thread before the
                # view provider receives a restored/cached BRep. This avoids
                # parallel display meshing stalls; the exact solid is retained.
                if App.GuiUp and not shape.isNull():
                    try:shape.tessellate(.1)
                    except MemoryError:raise
                    except Exception:pass  # Display preparation cannot discard a valid solid.
                obj.Shape=shape
                obj.Placement=placement
                self._shape_writes=getattr(self,'_shape_writes',0)+1
            if manifest:
                for name in ('ComponentCache','ComponentBRep','ComponentDocumentDigest'):
                    if name not in obj.PropertiesList:
                        obj.addProperty('App::PropertyString',name,'RotorForge','Verified incremental geometry cache',8);obj.setEditorMode(name,2)
                payload=component_payload(role,p)
                digest=current if unchanged else hashlib.sha256(obj.Shape.exportBrepToString().encode()).hexdigest()
                for name,value in (('ComponentCache',manifest),('ComponentBRep',payload),('ComponentDocumentDigest',digest)):
                    if str(getattr(obj,name))!=value:setattr(obj,name,value)
            if App.GuiUp:apply_material(obj.ViewObject,role,CARBON_ROLES,p)
            if role in ('LiPoPad','BatteryEnvelope','FrameCGMarker'):
                obj.Label={'LiPoPad':'LiPo pad (separate material)','BatteryEnvelope':('LiPo reference (detailed)' if p.DetailedBatteryReference else '1300 mAh LiPo reference (editable)'),'FrameCGMarker':'Active CG (nominal estimate)'}[role]
                if App.GuiUp:obj.ViewObject.Visibility=p.LiPoPadEnabled if role=='LiPoPad' else p.ShowReferences and (p.BatteryReferenceEnabled if role=='BatteryEnvelope' else p.ShowFrameCG)
            elif role in ('MotorEnvelopes','PropellerDiscs','StackEnvelope'):
                from .reference_options import enabled
                obj.Label={'MotorEnvelopes':'Motor references','PropellerDiscs':'Propeller references','StackEnvelope':'FC / ESC stack reference'}[role]+(' (detailed)' if enabled(p,role) else ' (simple)')
                if App.GuiUp:obj.ViewObject.Visibility=p.ShowReferences
            elif role in FLEX_ROLES:
                obj.Label={"CameraPadLeft":"Camera isolation left","CameraPadRight":"Camera isolation right"}.get(role,role.replace("MotorProtector","Motor protector ").replace("ElectronicsGuard","Electronics guard "))
                if App.GuiUp:obj.ViewObject.Visibility=role in flex_roles(p)
            elif role == "MidPlate":
                obj.Label = "Mid plate" if three_plate(p) else "Mid plate (unused in 2-plate mode)"
                if App.GuiUp:
                    obj.ViewObject.Visibility = three_plate(p)
            elif role in CAMERA_ROLES or role in ('CameraEnvelope','VTXEnvelope'):
                if role=='VTXEnvelope':obj.Label='VTX reference'+(' (detailed)' if p.DetailedVTXReference else ' (simple)')
                if role=='CameraEnvelope':obj.Label='FPV camera reference'+(' (detailed)' if p.DetailedCameraReference else ' (simple)')
                if role in CAMERA_ROLES:
                    obj.Label='Camera side plate '+('left' if role.endswith('Left') else 'right')
                if App.GuiUp:
                    obj.ViewObject.Visibility = p.FPVEnabled and (role in CAMERA_ROLES or p.ShowReferences)
            elif role in ARM_LOCK_ROLES+LEGACY_ARM_ROLES:
                obj.Label={'ArmKeystone':'Arm locking keystone','ArmClampPlate':'Upper arm clamp / FC stack plate',
                           'ArmLowerClampPlate':'Lower arm clamp plate',
                           'FrontArmBrace':'Old front clamp (replaced)','RearArmBrace':'Old rear clamp (replaced)'}[role]
                if App.GuiUp:
                    obj.ViewObject.Visibility=role in carbon_roles(p)
        except Exception:
            # Never display an old cutting profile after a parameter edit fails.
            obj.Shape = Part.Shape()

    def dumps(self):
        return None

    def loads(self, state):
        pass

    __getstate__ = dumps
    __setstate__ = loads


class ParameterViewProvider:
    def __init__(self, view):
        view.Proxy = self

    def attach(self, view):
        self.Object = view.Object

    def getIcon(self):
        return ICON

    def doubleClicked(self, view):
        from .gui import show_editor
        show_editor(view.Object)
        return True

    def dumps(self):
        return None

    def loads(self, state):
        pass

    __getstate__ = dumps
    __setstate__ = loads


from .flex_options import FLEX_ROLES,FLEX_OPTIONS
from .flex import flex_roles
from .appearance import apply_material


def ensure_components(settings):
    """Add optional parts when updating a document created by an older version."""
    p=read_parameters(settings)
    existing=component_objects(settings)
    group=next((parent for parent in settings.InList if 'Generator' in parent.PropertiesList and parent.Generator==settings),None)
    for role in ALL_ROLES:
        if role in existing:
            if App.GuiUp:apply_material(existing[role].ViewObject,role,CARBON_ROLES,p)
            continue
        obj=settings.Document.addObject('Part::FeaturePython',role)
        PartProxy(obj,settings,role)
        if group: group.addObject(obj)
        if App.GuiUp:
            view=obj.ViewObject
            view.Proxy=0
            view.Visibility=True
            view.ShapeColor=(.16,.19,.23) if role in CARBON_ROLES else (.78,.80,.83)
            view.LineColor=(.05,.07,.10)
            if role=='PropellerDiscs':
                view.ShapeColor,view.Transparency=(.18,.70,.82),86
            elif role=='MotorEnvelopes':
                view.ShapeColor,view.Transparency=(.42,.46,.52),50
            elif role=='LiPoPad':
                view.ShapeColor=(.13,.16,.18)
            elif role=='BatteryEnvelope':
                view.ShapeColor,view.Transparency=(.91,.45,.12),65
            elif role=='FrameCGMarker':
                view.ShapeColor=(.95,.13,.15)
            elif role=='StackEnvelope':
                view.ShapeColor,view.Transparency=(.20,.68,.36),68
            elif role=='CameraEnvelope':
                view.ShapeColor,view.Transparency=(.18,.21,.25),15
            elif role=='VTXEnvelope':
                view.ShapeColor,view.Transparency=(.58,.27,.68),35
            apply_material(view,role,CARBON_ROLES,p)


def create_frame(p=None, doc=None):
    p = p or Parameters()
    require_valid(p)
    invalidate_failed_build(p)
    # Build first: errors cannot leave an incomplete document tree.
    from .geometry import build_for_update,build_report
    build_for_update(p)
    doc = doc or App.ActiveDocument or App.newDocument("RotorForge")
    doc.openTransaction("Create RotorForge frame")
    try:
        group = doc.addObject("App::DocumentObjectGroup", "RotorForge")
        group.Label = "RotorForge — " + p.Layout + " — " + p.PlateDesign
        settings = doc.addObject("App::FeaturePython", "FrameParameters")
        settings.Label = "Frame Parameters (double-click to edit)"
        ParameterProxy(settings, p)
        settings.Proxy._pending_report=build_report(p)
        group.addObject(settings)
        group.addProperty("App::PropertyLink", "Generator", "RotorForge", "Frame parameter object").Generator = settings
        group.setEditorMode("Generator", 1)
        if App.GuiUp:
            ParameterViewProvider(settings.ViewObject)
        ensure_components(settings)
        doc.recompute()
        if not str(settings.Status).startswith("Valid"):
            raise ValueError(str(settings.Status))
        doc.commitTransaction()
        if App.GuiUp:
            from .view import view_front
            view_front()
        return settings
    except Exception:
        doc.abortTransaction()
        raise


def update_frame(settings, p):
    # A colour edit belongs to the view layer, even on a saved frame. Keep
    # ordinary no-op Update behavior so explicit geometry repairs still work.
    current=read_parameters(settings)
    from dataclasses import replace
    if p.PrintedPartColour!=current.PrintedPartColour and replace(current,PrintedPartColour=p.PrintedPartColour)==p and isinstance(settings.Proxy,ParameterProxy) and str(settings.Status).startswith('Valid'):
        require_valid(p);doc=settings.Document;doc.openTransaction('Colour RotorForge printed parts')
        try:
            if 'PrintedPartColour' not in settings.PropertiesList:
                settings.addProperty('App::PropertyEnumeration','PrintedPartColour','15 Appearance','Shared printed-part display colour')
                settings.PrintedPartColour=list(ENUMERATIONS['PrintedPartColour'])
            settings.PrintedPartColour=p.PrintedPartColour
            settings.Proxy._restored_signature=p.signature();settings.Proxy._last_full_signature=p.signature()
            apply_document_appearance(settings,p);doc.recompute();doc.commitTransaction();return
        except Exception:doc.abortTransaction();raise
    from .geometry import prime_document_cache
    prime_document_cache(settings)
    require_valid(p)
    invalidate_failed_build(p)
    from .geometry import build_for_update,build_report
    build_for_update(p)
    doc = settings.Document
    doc.openTransaction("Edit RotorForge frame")
    try:
        # A document can retain its properties and cached shapes even when its
        # saved Python proxy is unavailable. Rebind our stateless proxies so an
        # editor update restores parametric editing and canonical persistence.
        for obj in list(component_objects(settings).values()):
            if normalise_role(obj.FrameRole) not in ALL_ROLES:doc.removeObject(obj.Name)
        for name in list(settings.PropertiesList):
            if name=='FrameStyle' or (settings.getGroupOfProperty(name).startswith('12 ') and name not in Parameters.__dataclass_fields__) or name in RETIRED_PARAMETERS:settings.removeProperty(name)
        if not isinstance(settings.Proxy, ParameterProxy):
            settings.Proxy = ParameterProxy.__new__(ParameterProxy)
        for obj in component_objects(settings).values():
            if not isinstance(obj.Proxy, PartProxy):
                obj.Proxy = PartProxy.__new__(PartProxy)
        if App.GuiUp and not isinstance(settings.ViewObject.Proxy, ParameterViewProvider):
            ParameterViewProvider(settings.ViewObject)
        set_parameters(settings, p)
        ensure_components(settings)
        # An old file may already contain the new default values after migration.
        # Applying the editor must still replace its cached 0.1 geometry.
        settings.Proxy._pending_report=build_report(p)
        settings.touch()
        doc.recompute()
        if not str(settings.Status).startswith("Valid"):
            raise ValueError(str(settings.Status))
        for parent in settings.InList:
            if "Generator" in parent.PropertiesList and parent.Generator == settings:
                parent.Label = "RotorForge — " + p.Layout + " — " + p.PlateDesign
        from .hardware_refs import sync_refs,invalidate_refs
        try:sync_refs(settings)
        except Exception as reference_error:
            invalidate_refs(settings)
            App.Console.PrintWarning('RotorForge hardware references: '+str(reference_error)+'\n')
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise


def frame_parameters(obj):
    if 'SourceFrame' in obj.PropertiesList and obj.SourceFrame and 'GeneratorVersion' in obj.SourceFrame.PropertiesList:
        return obj.SourceFrame
    if 'SourcePart' in obj.PropertiesList and obj.SourcePart:
        return frame_parameters(obj.SourcePart)
    if "GeneratorVersion" in obj.PropertiesList:
        return obj
    if "Generator" in obj.PropertiesList:
        return obj.Generator
    if "Parameters" in obj.PropertiesList and obj.Parameters and "GeneratorVersion" in obj.Parameters.PropertiesList:
        return obj.Parameters
    return None


def find_parameters(selection=()):
    for obj in selection:
        found = frame_parameters(obj)
        if found:
            return found
    if App.ActiveDocument:
        found = [obj for obj in App.ActiveDocument.Objects if "GeneratorVersion" in obj.PropertiesList]
        if len(found) == 1:
            return found[0]
    raise ValueError("Select a RotorForge frame, its parameter object, or one of its parts.")


def component_objects(settings):
    return {normalise_role(obj.FrameRole): obj for obj in settings.Document.Objects
            if "Parameters" in obj.PropertiesList and obj.Parameters == settings and "FrameRole" in obj.PropertiesList}


