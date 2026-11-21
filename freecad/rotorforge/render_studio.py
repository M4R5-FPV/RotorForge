"""On-demand image export; no geometry feature or document recompute."""
import json, math, os, shutil, tempfile
from pathlib import Path
import FreeCAD as App
import FreeCADGui as Gui
try:
    from PySide import QtCore, QtGui, QtWidgets
except ImportError:
    try: from PySide2 import QtCore, QtGui, QtWidgets
    except ImportError: from PySide6 import QtCore, QtGui, QtWidgets

from .paths import icon_path
from .coin_support import initialize_coin
from .render_quality import QUALITY_NAMES, QUALITY_PRESETS, MESH_DETAILS, quality_options
from .render_presets import (NAMES, PRESETS, POSE_NAMES, POSES, source_palette, hardware_surface,
                             RIG_NAMES, LIGHT_COLOUR_KEYS, CONTRAST_NAMES, lighting_settings,
                             linear_to_srgb, srgb_to_linear)


from .blender_discovery import (find_blender, normalize_choice, launch_command,
                                FLATPAK_CHOICE, flatpak_temp_parent, stage_flatpak_job)


def visible_parts(settings):
    from .document import component_objects
    from .hardware_refs import objects
    parts=list(component_objects(settings).items())+[(str(getattr(o,'HardwareRole',o.Name)),o) for o in objects(settings)]
    return [(r,o) for r,o in parts if r!='FrameCGMarker' and o.ViewObject.Visibility and not o.Shape.isNull()]


def scene_payload(settings, parts, options):
    from .document import read_parameters
    from .geometry import carbon_roles
    from .appearance import (arm_texture_angle, carbon_texture_path, carbon_edge_texture_path,
                             CARBON_COLOR, printed_finish, FLEX_ROLES)
    from .prop_palette import prop_finish, prop_optics
    from .motor_palette import MOTOR_BELL, reference_face_colours
    from .reference_options import enabled, FLAGS, SIMPLE
    p=read_parameters(settings); carbon=set(carbon_roles(p)); result=[]; propellers=[]
    textured=bool(p.CarbonTextureEnabled and p.CarbonTextureOpacity>0)
    for role,obj in parts:
        view=obj.ViewObject; shape=obj.Shape; faces=shape.Faces
        base,colors=None,()
        alpha=1-float(view.Transparency)/100
        fixed=None;surface='generic';metal_colours=();bell_faces=();optics=None
        if hardware_surface(role,obj.PropertiesList):surface='metal'
        elif role in carbon:fixed=CARBON_COLOR;surface='carbon'
        elif role in ('LiPoPad',)+FLEX_ROLES or (role in ('CameraMountLeft','CameraMountRight') and p.CameraCageStyle=='TPU cage'):
            fixed,trans=printed_finish(p);alpha=1-trans/100;surface='tpu'
        elif role=='PropellerDiscs' and enabled(p,role):
            fixed,trans=prop_finish(p.PropReferenceColour);alpha=1-trans/100;surface='prop';optics=prop_optics(p.PropReferenceColour)
        elif role in FLAGS:
            if enabled(p,role):
                # Use the same cached per-face finish table that the native
                # reference model uses; do not rely on stale GUI grey defaults.
                from .detailed_references import _placed_reference, METAL, COPPER
                _,palette=_placed_reference(p,role)
                if len(palette)==len(faces):
                    if role=='MotorEnvelopes':
                        bell_faces=tuple(c==MOTOR_BELL for c in palette)
                        colors=reference_face_colours(palette,p.MotorReferenceColour)
                    else:colors=palette
                metal_colours=(METAL,COPPER)
                alpha=1.
            else:
                fixed,trans=SIMPLE[role];alpha=1-trans/100
        elif role in ('VTXAntennaReference','ELRSTReference'):
            from .antenna_reference_models import antenna_reference,reference_enabled
            if reference_enabled(p,role):
                _,palette=antenna_reference(p,role)
                if len(palette)==len(faces):colors=palette
        elif role in ('CameraMountLeft','CameraMountRight'):
            fixed=(.68,.70,.73);surface='metal'
        if fixed is not None:base=tuple(fixed);colors=()
        else:
            base,source_colors=source_palette(view,len(faces))
            if not colors:colors=source_colors
        if role=='PropellerDiscs' and options.get('spinning') and options.get('blur',0)>0:
            from .parameters import motor_centres, arms_above_bottom
            from .reference_options import PROP_HUB_HEIGHT, PROP_BORE
            detailed=enabled(p,role)
            prop_base=(p.BottomThickness if arms_above_bottom(p) else -p.ArmThickness)+p.ArmThickness+(p.MotorReferenceHeight if detailed else p.PropReferenceHeight)
            radius=p.PropDiameter/2
            color,trans=prop_finish(p.PropReferenceColour) if detailed else SIMPLE[role]
            for x,y in motor_centres(p):
                propellers.append(dict(center=[x*.001,y*.001,(prop_base+(PROP_HUB_HEIGHT/2 if detailed else .125))*.001],radius=radius*.001,hub=max(4.,min(8.,radius*.105))*.001,hub_height=PROP_HUB_HEIGHT*.001 if detailed else .00025,bore=PROP_BORE*.0005,color=color,detailed=detailed,alpha=1-trans/100,optics=optics))
            continue
        verts=[]; tris=[]; groups=[]; mats=[]; mat_index={}
        for i,face in enumerate(faces):
            color=tuple(float(colors[i][k]) for k in range(3)) if len(colors)==len(faces) else base
            planar=type(face.Surface).__name__=='Plane'; side=role.startswith('CameraMount')
            kind='plain'
            if role in carbon and textured:
                n=face.normalAt(0,0) if planar else None
                kind='weave' if n is not None and abs(n.y if side else n.z)>.985 else 'edge'
            bell=bool(bell_faces and bell_faces[i]);metal=bell or color in metal_colours
            face_surface='motor_bell' if bell else surface
            key=(color,kind,metal,face_surface)
            if key not in mat_index:mat_index[key]=len(mats);mats.append({'color':color,'kind':kind,'metal':metal,'surface':face_surface})
            points,triangles=face.tessellate(options['deflection']); start=len(verts)
            verts.extend((float(v.x)*.001,float(v.y)*.001,float(v.z)*.001) for v in points)
            for tri in triangles:
                if len(set(tri))!=3:continue
                tris.append([start+int(k) for k in tri]);groups.append([mat_index[key],not planar])
        if not tris:continue
        result.append(dict(name=obj.Label,role=role,vertices=verts,triangles=tris,groups=groups,materials=mats,alpha=alpha,angle=arm_texture_angle(role,p),side=role.startswith('CameraMount'),surface=surface,optics=optics))
    if not result and not propellers:raise ValueError('No visible renderable parts in the selected frame.')
    return dict(parts=result,propellers=propellers,options=options,texture=carbon_texture_path(),edge_texture=carbon_edge_texture_path(),tile=p.CarbonTextureTile*.001,texture_opacity=p.CarbonTextureOpacity/100 if p.CarbonTextureEnabled else 0)


class RenderDialog(QtWidgets.QDialog):
    def __init__(self,settings,parent=None):
        super().__init__(parent);self.settings=settings;self.setWindowTitle('RotorForge — Render Studio (experimental)');self.resize(540,480);self._ui_ready=False
        outer=QtWidgets.QVBoxLayout(self);scroll=QtWidgets.QScrollArea();scroll.setWidgetResizable(True);panel=QtWidgets.QWidget();form=QtWidgets.QFormLayout(panel);self._form=form;scroll.setWidget(panel);outer.addWidget(scroll)
        def combo(label,items):
            w=QtWidgets.QComboBox();w.addItems(items);form.addRow(label,w);return w
        def integer(label,lo,hi,value):
            w=QtWidgets.QSpinBox();w.setRange(lo,hi);w.setValue(value);form.addRow(label,w);return w
        def number(label,lo,hi,value,step=.1):
            w=QtWidgets.QDoubleSpinBox();w.setRange(lo,hi);w.setValue(value);w.setSingleStep(step);form.addRow(label,w);return w
        self.engine=combo('Engine',['Quick Render (FreeCAD)','Studio Render (Blender)'])
        self.style=combo('Look preset',list(NAMES)+['Custom'])
        self._base_style=0;self._applying=False
        self.reset_preset=QtWidgets.QPushButton('Reset to preset defaults');form.addRow(self.reset_preset)
        self.background=combo('Background',['Studio / current','Transparent','White','Black'])
        self.res=combo('Resolution',['1920 × 1080','3840 × 2160','7680 × 4320','Custom']);self.width=integer('Width (px)',128,8192,1920);self.height=integer('Height (px)',128,8192,1080)
        self.pose=combo('Pose preset',list(POSE_NAMES)+['Custom']);self._base_pose=0;self._posing=False
        self.reset_pose=QtWidgets.QPushButton('Reset pose');form.addRow(self.reset_pose)
        self.camera=combo('Camera',['Current viewport','Front three-quarter','Rear three-quarter','Top','Side','Custom','Match FreeCAD viewport'])
        self.az=number('Azimuth (°; nose = 0)',-180,180,35,5);self.el=number('Elevation (°)',5,90,30,5)
        self.zoom=number('Framing / zoom (1 = auto fit)',.35,1,1);self.lens=integer('Focal length (mm)',18,120,42)
        self.projection=combo('Studio projection',['Perspective (natural depth)','Orthographic (CAD style)'])
        self.viewport_note=QtWidgets.QLabel('Matches the current FreeCAD camera position, projection, field of view and pan. Zoom 1 preserves framing; a different output aspect or clipped parts may widen the view.');self.viewport_note.setWordWrap(True);form.addRow(self.viewport_note)
        self.flying=QtWidgets.QCheckBox();form.addRow('Flight pose / floating drone',self.flying)
        self.pitch=number('Forward pitch (°)',-60,60,0,1);self.roll=number('Roll (°)',-60,60,0,1);self.yaw=number('Drone yaw (°)',-180,180,0,5)
        self.spinning=QtWidgets.QCheckBox();form.addRow('Spinning propellers',self.spinning)
        self.blur=number('Prop blur amount',0,1,.62,.05)
        self.flight_shadow=QtWidgets.QCheckBox();self.flight_shadow.setChecked(True);form.addRow('Floating shadow',self.flight_shadow)
        self.flight_height=number('Flight height (relative to drone size)',.05,2,.26,.05)
        self.flight_bias=number('Forward composition margin',0,.10,0,.01)
        self.flight_note=QtWidgets.QLabel('Flight effects are Blender-only. Enable visible prop references to render spinning props. Floating shadows require a ground plane and a non-transparent background.');self.flight_note.setWordWrap(True);form.addRow(self.flight_note)
        self.key=number('Key light intensity',0,4,1);self.fill=number('Fill light intensity',0,3,.16);self.rim=number('Rim light intensity',0,4,.95);self.world=number('Ambient / world strength',0,2,.12,.05);self.soft=number('Light softness',.2,3,1)
        self.exposure=number('Exposure (EV)',-4,4,0);self.rough=number('Material roughness multiplier',.35,2,1);self.ground_rough=number('Ground roughness',.05,1,.38,.05)
        self.floor=QtWidgets.QCheckBox();self.floor.setChecked(True);form.addRow('Ground plane',self.floor)
        self.lighting_toggle=QtWidgets.QCheckBox('Show advanced lighting & colours');form.addRow(self.lighting_toggle)
        self.lighting_panel=QtWidgets.QGroupBox('Advanced lighting & colours');lighting_form=QtWidgets.QFormLayout(self.lighting_panel)
        self.rig=QtWidgets.QComboBox();self.rig.addItems(RIG_NAMES);lighting_form.addRow('Light arrangement',self.rig)
        self.accent=QtWidgets.QDoubleSpinBox();self.accent.setRange(0,4);self.accent.setSingleStep(.05);lighting_form.addRow('Accent light intensity',self.accent)
        self.contrast=QtWidgets.QComboBox();self.contrast.addItems([name.replace('AgX - ','') for name in CONTRAST_NAMES]);lighting_form.addRow('Tonal contrast',self.contrast)
        self._light_colors={};self._color_buttons={}
        for key,label in zip(LIGHT_COLOUR_KEYS,('Key light colour','Fill light colour','Rim light colour','Accent light colour','Ambient light colour','Studio backdrop colour','Studio floor colour')):
            w=QtWidgets.QPushButton();self._color_buttons[key]=w;lighting_form.addRow(label,w)
            w.clicked.connect(lambda checked=False,k=key:self.choose_light_color(k))
        lighting_note=QtWidgets.QLabel('Colours affect the lighting and studio environment, not the CAD materials. Backdrop and floor colours apply to Studio / current background; White, Black and Transparent override the background.');lighting_note.setWordWrap(True);lighting_form.addRow(lighting_note)
        form.addRow(self.lighting_panel)
        self.lighting_toggle.toggled.connect(self.sync)
        self.rig.currentIndexChanged.connect(self.mark_custom);self.accent.valueChanged.connect(self.mark_custom);self.contrast.currentIndexChanged.connect(self.mark_custom)
        self.quality=combo('Render quality',list(QUALITY_NAMES)+['Custom']);self._quality_applying=False
        self.samples=integer('Maximum Cycles samples',8,4096,512)
        self.minimum_samples=integer('Minimum Cycles samples',1,4096,64)
        self.noise_threshold=number('Noise threshold',.001,.10,.005,.001);self.noise_threshold.setDecimals(4);self.noise_threshold.setRange(.001,.10);self.noise_threshold.setSingleStep(.001)
        self.filter_width=number('Pixel filter width (px)',.75,2.5,1.,.05)
        self.denoise=QtWidgets.QCheckBox();self.denoise.setChecked(True);form.addRow('Denoise final image',self.denoise)
        self.detail=combo('Mesh detail',[name for name,_ in MESH_DETAILS])
        self.device=combo('Cycles device',['Auto (OptiX / CUDA / CPU)','CPU','OptiX','CUDA'])
        self.quality_note=QtWidgets.QLabel('High and Ultra Quality use more samples, finer CAD meshes and a narrower pixel filter to preserve detail. Resolution is independent; 4K PNG is recommended for final images. Preview uses fast settings.');self.quality_note.setWordWrap(True);form.addRow(self.quality_note)
        self.quality.currentIndexChanged.connect(self.apply_quality)
        for w in (self.samples,self.minimum_samples,self.noise_threshold,self.filter_width):w.valueChanged.connect(self.mark_quality_custom)
        self.detail.currentIndexChanged.connect(self.mark_quality_custom);self.denoise.toggled.connect(self.mark_quality_custom)
        self.apply_quality(2)
        row=QtWidgets.QWidget();lay=QtWidgets.QHBoxLayout(row);lay.setContentsMargins(0,0,0,0)
        self.blender=QtWidgets.QLineEdit();pref=App.ParamGet('User parameter:BaseApp/Preferences/Mod/RotorForge');self.blender.setText(find_blender(pref.GetString('BlenderPath','')));browse=QtWidgets.QPushButton('Browse…');detect=QtWidgets.QPushButton('Auto-detect');lay.addWidget(self.blender);lay.addWidget(browse);lay.addWidget(detect);form.addRow('Blender executable',row)
        self._blender_choice=self.blender.text()
        self.blender.setPlaceholderText('No Blender detected — browse or auto-detect')
        self.blender.setToolTip('Executable path, macOS .app bundle, or detected Flatpak installation. A valid manually selected path is remembered.')
        detect.clicked.connect(self.detect_blender)
        browse.clicked.connect(self.browse)
        self.note=QtWidgets.QLabel('Quick Render captures the existing shaded view. Studio Render creates a separate lighting scene using visible frame parts and hardware. Perspective uses the focal length control; lower mm values create a stronger perspective effect, while Orthographic keeps the CAD-style parallel view.');self.note.setWordWrap(True);form.addRow(self.note)
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close);render=buttons.addButton('Render image…',QtWidgets.QDialogButtonBox.ActionRole);preview=buttons.addButton('Preview (960 px)…',QtWidgets.QDialogButtonBox.ActionRole);outer.addWidget(buttons)
        buttons.rejected.connect(self.reject);render.clicked.connect(lambda: self.run(False));preview.clicked.connect(lambda: self.run(True))
        self._preset_fields={key:getattr(self,key) for key in ('key','fill','rim','world','soft','exposure','rough','ground_rough','background','floor')}
        self.style.currentIndexChanged.connect(self.apply_preset);self.reset_preset.clicked.connect(lambda: self.apply_preset(self._base_style))
        for key,w in self._preset_fields.items():
            signal=w.currentIndexChanged if key=='background' else w.toggled if key=='floor' else w.valueChanged
            signal.connect(self.mark_custom)
        self.apply_preset(0)
        self._pose_fields={key:getattr(self,key) for key in POSES[0]}
        self.pose.currentIndexChanged.connect(self.apply_pose);self.reset_pose.clicked.connect(lambda:self.apply_pose(self._base_pose))
        for key,w in self._pose_fields.items():
            signal=w.toggled if key in ('spinning','flying','flight_shadow') else w.currentIndexChanged if key=='projection' else w.valueChanged
            signal.connect(self.mark_pose_custom)
        self.camera.currentIndexChanged.connect(self.mark_pose_custom)
        self.flying.toggled.connect(self.sync);self.spinning.toggled.connect(self.sync)
        self.apply_pose(0)
        self._studio_only=(self.style,self.reset_preset,self.pose,self.reset_pose,self.lens,self.projection,
            self.flying,self.pitch,self.roll,self.yaw,self.spinning,self.blur,self.flight_shadow,
            self.flight_height,self.flight_bias,self.flight_note,self.key,self.fill,self.rim,self.world,
            self.soft,self.exposure,self.rough,self.ground_rough,self.floor,self.quality,self.samples,
            self.minimum_samples,self.noise_threshold,self.filter_width,self.denoise,self.detail,
            self.device,self.quality_note,self.lighting_toggle)
        self.res.currentIndexChanged.connect(self.resolution);self.engine.currentIndexChanged.connect(self.sync);self.camera.currentIndexChanged.connect(self.sync);self.projection.currentIndexChanged.connect(self.sync)
        if self._blender_choice:self.engine.setCurrentIndex(1);self.camera.setCurrentIndex(6);self.res.setCurrentIndex(1)
        else:self.camera.setCurrentIndex(0)
        self._ui_ready=True
        self.blender.textChanged.connect(self.refresh_blender)
        self.refresh_blender()
    def _row_visible(self,w,visible):
        # Qt 6.4+ supports hiding a whole form row. Older FreeCAD/PySide
        # versions need both the field and its label hidden explicitly.
        if hasattr(self._form,'setRowVisible'):
            self._form.setRowVisible(w,visible)
        else:
            label=self._form.labelForField(w)
            if label is not None:label.setVisible(visible)
            w.setVisible(visible)
    def refresh_blender(self,*args):
        # Validate only the edited path. Full installation discovery is reserved
        # for startup, Auto-detect and launch recovery, not every UI signal.
        was_ready=bool(self._blender_choice)
        self._blender_choice=normalize_choice(self.blender.text())
        ready=bool(self._blender_choice)
        if not ready:
            self.engine.setCurrentIndex(0)
            if self.engine.count()>1:self.engine.removeItem(1)
            if self.camera.currentIndex()==6:self.camera.setCurrentIndex(0)
            if self.camera.count()>6:self.camera.removeItem(6)
        else:
            if self.engine.count()==1:self.engine.addItem('Studio Render (Blender)')
            if self.camera.count()==6:self.camera.addItem('Match FreeCAD viewport')
            if not was_ready:
                self.engine.setCurrentIndex(1);self.camera.setCurrentIndex(6)
        self.sync()
    def apply_quality(self,i):
        if self._quality_applying or not 0<=i<len(QUALITY_PRESETS):return
        self._quality_applying=True
        try:
            samples,minimum,threshold,width,detail,denoise=QUALITY_PRESETS[i]
            self.quality.setCurrentIndex(i);self.samples.setValue(samples);self.minimum_samples.setValue(minimum)
            self.noise_threshold.setValue(threshold);self.filter_width.setValue(width);self.detail.setCurrentIndex(detail);self.denoise.setChecked(denoise)
        finally:self._quality_applying=False
    def mark_quality_custom(self,*args):
        if not self._quality_applying:self.quality.setCurrentIndex(len(QUALITY_PRESETS))
    def apply_preset(self,i):
        if self._applying or not 0<=i<len(PRESETS):return
        self._applying=True
        try:
            self._base_style=i;self.style.setCurrentIndex(i)
            for key,value in PRESETS[i].items():
                w=self._preset_fields[key]
                if key=='background':w.setCurrentIndex(value)
                elif key=='floor':w.setChecked(value)
                else:w.setValue(value)
            lighting=lighting_settings(i)
            self.rig.setCurrentIndex(lighting['rig']);self.accent.setValue(lighting['accent'])
            self.contrast.setCurrentIndex(CONTRAST_NAMES.index(lighting['look']))
            for key in LIGHT_COLOUR_KEYS:self.set_light_color(key,lighting[key])
            self.style.setToolTip('Base lighting: '+NAMES[i]);self.reset_preset.setText('Reset to '+NAMES[i])
        finally:self._applying=False
    def set_light_color(self,key,color):
        # Store linear values exactly; swatches use display sRGB. Only actual
        # picker edits are converted back into scene-linear values.
        self._light_colors[key]=tuple(color)
        rgb=linear_to_srgb(color);qcolor=QtGui.QColor.fromRgbF(*rgb)
        text=qcolor.name().upper();button=self._color_buttons[key]
        button.setText(text);button.setStyleSheet('QPushButton { background-color: '+text+'; color: '+('#111111' if .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]>.55 else '#ffffff')+'; }')
    def choose_light_color(self,key):
        current=QtGui.QColor.fromRgbF(*linear_to_srgb(self._light_colors[key]))
        selected=QtWidgets.QColorDialog.getColor(current,self,'Choose studio colour')
        if selected.isValid():
            self.set_light_color(key,srgb_to_linear((selected.redF(),selected.greenF(),selected.blueF())))
            self.mark_custom()
    def light_options(self):
        return dict(self._light_colors,rig=self.rig.currentIndex(),accent=self.accent.value(),look=CONTRAST_NAMES[self.contrast.currentIndex()])
    def mark_custom(self,*args):
        if not self._applying and self.engine.currentIndex()==1:self.style.setCurrentIndex(len(PRESETS))
    def apply_pose(self,i):
        if self._posing or not 0<=i<len(POSES):return
        self._posing=True
        try:
            self._base_pose=i;self.pose.setCurrentIndex(i);self.camera.setCurrentIndex(5)
            for key,value in POSES[i].items():
                w=self._pose_fields[key]
                if key in ('spinning','flying','flight_shadow'):w.setChecked(value)
                elif key=='projection':w.setCurrentIndex(value)
                else:w.setValue(value)
            self.reset_pose.setText('Reset to '+POSE_NAMES[i])
        finally:self._posing=False
        self.sync()
    def mark_pose_custom(self,*args):
        if not self._posing:self.pose.setCurrentIndex(len(POSES))
    def detect_blender(self):
        detected=find_blender()
        if detected:
            self.blender.setText(detected);self.engine.setCurrentIndex(1)
        else:
            self.refresh_blender()
            QtWidgets.QMessageBox.information(self,'Blender detection','No Blender installation found in the usual locations. Use Browse to select the executable manually.')
    def browse(self):
        current=self.blender.text()
        start=current if current and current!=FLATPAK_CHOICE else str(Path.home())
        p,_=QtWidgets.QFileDialog.getOpenFileName(self,'Select Blender executable',start)
        if p:
            detected=normalize_choice(p)
            if detected:
                self.blender.setText(detected);self.engine.setCurrentIndex(1)
            else:QtWidgets.QMessageBox.warning(self,'Blender detection','Select an accessible Blender executable, not a shortcut or installer.')
    def resolution(self,i):
        if i<3:self.width.setValue([1920,3840,7680][i]);self.height.setValue([1080,2160,4320][i])
    def sync(self,*args):
        if not self._ui_ready:return
        studio=bool(self._blender_choice) and self.engine.currentIndex()==1
        # Shared Quick Render fields (background, resolution, camera and zoom)
        # and the executable path/discovery row remain usable in every mode.
        for w in self._studio_only:self._row_visible(w,studio)
        self._row_visible(self.lighting_panel,studio and self.lighting_toggle.isChecked())
        match=studio and self.camera.currentIndex()==6
        self._row_visible(self.viewport_note,match)
        self.projection.setEnabled(studio and not match)
        self.lens.setEnabled(studio and not match and self.projection.currentIndex()==0)
        for w in (self.az,self.el):w.setEnabled(self.camera.currentIndex()==5)
        for w in (self.pitch,self.roll,self.yaw,self.flight_shadow,self.flight_height,self.flight_bias):w.setEnabled(studio and self.flying.isChecked())
        self.blur.setEnabled(studio and self.spinning.isChecked())
        if studio:
            self.note.setText('Studio Render uses visible frame parts and hardware. Perspective uses focal length; lower mm values create a stronger perspective effect.')
        elif self._blender_choice:
            self.note.setText('Quick Render captures the existing shaded FreeCAD view.')
        else:
            self.note.setText('Quick Render captures the existing shaded FreeCAD view. To enable Studio Render, install Blender and use Auto-detect or Browse, or enter its executable path.')
    def options(self,preview):
        w,h=self.width.value(),self.height.value()
        if preview:
            scale=min(1,960/max(w,h));w,h=max(128,round(w*scale)),max(128,round(h*scale))
        i=self.camera.currentIndex();az,el={1:(35,30),2:(145,30),3:(0,90),4:(90,10),5:(self.az.value(),self.el.value())}.get(i,(35,30))
        eye=[math.sin(math.radians(az))*math.cos(math.radians(el)),math.cos(math.radians(az))*math.cos(math.radians(el)),math.sin(math.radians(el))]
        up=[0,0,1] if el<89.9 else [0,1,0]
        viewport=None;orthographic=self.projection.currentIndex()==1
        if i in (0,6):
            view=Gui.activeDocument().activeView();rot=view.getCameraOrientation();e=rot.multVec(App.Vector(0,0,1));u=rot.multVec(App.Vector(0,1,0));eye=[e.x,e.y,e.z];up=[u.x,u.y,u.z]
            if i==6 and self.engine.currentIndex()==1:
                if initialize_coin() is None:
                    raise ValueError("Pivy/Coin3D is unavailable; choose a preset camera instead.")
                node=view.getCameraNode();vw,vh=view.getSize()
                if vw<=0 or vh<=0:raise ValueError('The FreeCAD viewport has no visible size.')
                orthographic=hasattr(node,'height')
                if not orthographic and not hasattr(node,'heightAngle'):raise ValueError('Unsupported FreeCAD camera type.')
                position=node.position.getValue().getValue()
                extent=float(node.height.getValue())*.001 if orthographic else float(node.heightAngle.getValue())
                viewport=dict(position=[float(v)*.001 for v in position],aspect=float(vw)/vh,extent=extent)
        flight=self.engine.currentIndex()==1 and self.flying.isChecked()
        return dict(viewport=viewport,flying=flight,pitch=self.pitch.value() if flight else 0.,roll=self.roll.value() if flight else 0.,yaw=self.yaw.value() if flight else 0.,spinning=self.engine.currentIndex()==1 and self.spinning.isChecked(),blur=self.blur.value(),flight_height=self.flight_height.value(),flight_shadow=self.flight_shadow.isChecked(),flight_bias=self.flight_bias.value() if flight else 0.,width=w,height=h,eye=eye,up=up,zoom=self.zoom.value(),lens=self.lens.value(),orthographic=orthographic,style=self._base_style,lighting=self.light_options(),background=self.background.currentIndex(),key=self.key.value(),fill=self.fill.value(),rim=self.rim.value(),world=self.world.value(),ground_rough=self.ground_rough.value(),soft=self.soft.value(),exposure=self.exposure.value(),rough=self.rough.value(),floor=self.floor.isChecked(),device=self.device.currentIndex(),**quality_options(self.samples.value(),self.minimum_samples.value(),self.noise_threshold.value(),self.filter_width.value(),self.detail.currentIndex(),self.denoise.isChecked(),preview))
    def run(self,preview):
        from .export_naming import image_name, available_image_path, pictures_directory
        studio=self.engine.currentIndex()==1
        look=(NAMES[self._base_style] + (' Custom' if self.style.currentIndex()==len(PRESETS) else '')) if studio else None
        folder=pictures_directory(QtCore.QStandardPaths)
        name=image_name(self.settings.Document, preview, look)
        suggestion=str(folder/name)
        filters='PNG image (*.png);;JPEG image (*.jpg *.jpeg)'
        if studio:
            path,selected=QtWidgets.QFileDialog.getSaveFileName(self,'Save rendered image',suggestion,filters,options=QtWidgets.QFileDialog.DontConfirmOverwrite)
        else:path,selected=QtWidgets.QFileDialog.getSaveFileName(self,'Save rendered image',suggestion,filters)
        if not path:return
        if not Path(path).suffix:path+=('.jpg' if selected.startswith('JPEG') else '.png')
        try:
            opt=self.options(preview)
            if opt['background']==1 and Path(path).suffix.lower()!='.png':raise ValueError('Transparency requires PNG.')
            choice=''
            if self.engine.currentIndex()==1:
                choice=find_blender(self.blender.text())
                if not choice:
                    self.blender.clear();self.refresh_blender()
                    raise ValueError('Blender 4.x or 5.x was not found. Install Blender or use Browse to select its executable. Quick Render needs no Blender.')
                self.blender.setText(choice)
            parent=flatpak_temp_parent() if choice==FLATPAK_CHOICE else None
            with tempfile.TemporaryDirectory(prefix='rotorforge_render_',dir=parent) as temp:
                output=Path(temp)/('image'+Path(path).suffix.lower())
                if self.engine.currentIndex()==0:self.quick(output,opt)
                else:
                    if not self.studio(output,opt,Path(temp),choice):return
                if not output.is_file() or output.stat().st_size==0:raise RuntimeError('Renderer did not create an image.')
                if studio:
                    # Reserve an unused name atomically; never overwrite an earlier Blender render.
                    requested=path
                    while True:
                        path=str(available_image_path(requested))
                        try:
                            target=open(path,'xb')
                        except FileExistsError:continue
                        try:
                            with target, output.open('rb') as source:shutil.copyfileobj(source,target)
                        except Exception:
                            Path(path).unlink(missing_ok=True);raise
                        break
                else:shutil.copyfile(output,path)
            QtWidgets.QMessageBox.information(self,'Render saved',path)
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
        except Exception as exc:QtWidgets.QMessageBox.warning(self,'Render Studio',str(exc))
    def quick(self,path,opt):
        view=Gui.activeDocument().activeView();saved=view.getCamera();visibility=[]
        try:
            # Only the selected frame and its currently visible hardware; no design edits.
            keep={o.Name for _,o in visible_parts(self.settings)}
            if not keep:raise ValueError('No visible frame parts.')
            for obj in self.settings.Document.Objects:
                if 'Shape' in obj.PropertiesList and obj.Name not in keep and obj.ViewObject.Visibility:
                    visibility.append(obj);obj.ViewObject.hide()
            if self.camera.currentIndex() not in (0,6):
                eye=App.Vector(*opt['eye']);up=App.Vector(*opt['up']);right=up.cross(eye);view.setCameraOrientation(App.Rotation(right,eye.cross(right),eye,'ZXY').Q);view.fitAll()
            try:
                camera_node=view.getCameraNode() if initialize_coin() is not None else None
                if hasattr(camera_node,'height'):camera_node.height.setValue(float(camera_node.height.getValue())/opt['zoom'])
                elif hasattr(camera_node,'heightAngle'):camera_node.heightAngle.setValue(float(camera_node.heightAngle.getValue())/opt['zoom'])
            except (AttributeError,RuntimeError):pass
            Gui.updateGui();view.saveImage(str(path),opt['width'],opt['height'],['Current','Transparent','White','Black'][opt['background']])
        finally:
            for obj in visibility:obj.ViewObject.show()
            view.setCamera(saved);Gui.updateGui()
    def studio(self,path,opt,temp,choice):
        script=Path(__file__).with_name('render_blender.py')
        self.note.setText('Preparing visible CAD meshes…');QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            payload=scene_payload(self.settings,visible_parts(self.settings),opt)
            if choice==FLATPAK_CHOICE:script=stage_flatpak_job(temp,payload,script)
            job=temp/'scene.json';job.write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8')
        finally:QtWidgets.QApplication.restoreOverrideCursor()
        process=QtCore.QProcess(self);process.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        progress=QtWidgets.QProgressDialog('Rendering in Blender Cycles…','Cancel',0,0,self);progress.setWindowModality(QtCore.Qt.WindowModal);progress.setMinimumDuration(0)
        log=[]
        def read():
            s=bytes(process.readAllStandardOutput()).decode('utf-8','replace');log.append(s)
            if len(log)>100:del log[:-100]
            # Keep the progress label static; retain output for error diagnostics.
        process.readyReadStandardOutput.connect(read);loop=QtCore.QEventLoop();process.finished.connect(lambda *_:loop.quit());progress.canceled.connect(process.kill)
        executable,args=launch_command(choice,temp,['--background','--factory-startup','--python-exit-code','1','--python',str(script),'--',str(job),str(path)])
        process.start(executable,args)
        if not process.waitForStarted(5000):raise RuntimeError('Could not start Blender: '+process.errorString())
        progress.show()
        if process.state()!=QtCore.QProcess.NotRunning:(loop.exec() if hasattr(loop,'exec') else loop.exec_())
        read();cancelled=progress.wasCanceled();progress.close();self.note.setText('Studio render uses the visible frame; ordinary frame generation is unchanged.')
        if cancelled:return False
        if process.exitCode()!=0 or not path.is_file():raise RuntimeError('Blender render failed:\n'+''.join(log)[-3500:])
        App.ParamGet('User parameter:BaseApp/Preferences/Mod/RotorForge').SetString('BlenderPath',choice)
        return True


class RenderCommand:
    def GetResources(self):return {'Pixmap':icon_path('render-studio.svg'),'MenuText':'Render Studio…','ToolTip':'Export high-resolution shaded or ray-traced product images'}
    def IsActive(self):return App.ActiveDocument is not None
    def Activated(self):
        from .document import find_parameters
        try:
            settings=find_parameters(Gui.Selection.getSelection());dialog=RenderDialog(settings,Gui.getMainWindow());dialog.exec() if hasattr(dialog,'exec') else dialog.exec_()
        except Exception as exc:QtWidgets.QMessageBox.warning(Gui.getMainWindow(),'RotorForge Render Studio',str(exc))
