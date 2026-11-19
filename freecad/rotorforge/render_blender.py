"""Executed only by external Blender 4+/5+, never imported into FreeCAD."""
import bpy, json, math, sys
from mathutils import Vector, Matrix
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from render_presets import LIGHT_RIGS, lighting_settings, fit_camera, area_power, surface_finish, flight_margins, blur_profile, viewport_half_height, viewport_safe_half_height

from render_quality import configure_cycles

job,output=sys.argv[sys.argv.index('--')+1:];data=json.loads(Path(job).read_text(encoding='utf-8'));o=data['options']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';configure_cycles(scene,o)
# Set output aspect before asking Blender for the actual camera frame.
scene.render.resolution_x=o['width'];scene.render.resolution_y=o['height'];scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
if o['device']!=1:
    pref=bpy.context.preferences.addons['cycles'].preferences
    for backend in (['OPTIX','CUDA'] if o['device']==0 else ['OPTIX' if o['device']==2 else 'CUDA']):
        try:
            pref.compute_device_type=backend;pref.refresh_devices();devices=[d for d in pref.devices if d.type==backend]
            if not devices:continue
            for d in pref.devices:d.use=(d.type==backend)
            scene.cycles.device='GPU';print('RotorForge device:',backend,flush=True);break
        except Exception as e:print(str(e),flush=True)
    else:
        if o['device']!=0:raise RuntimeError('Requested GPU backend unavailable. Choose Auto or CPU.')
        scene.cycles.device='CPU'
else:scene.cycles.device='CPU'


def lin(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4


def material(part,spec):
    kind=spec['kind'];role=part['role'];color=tuple(lin(max(0,min(1,v))) for v in spec['color']);clay=o['style']==3
    m=bpy.data.materials.new(part['name']+' '+kind);m.use_nodes=True;n=m.node_tree.nodes;links=m.node_tree.links;bs=n.get('Principled BSDF')
    surface=spec.get('surface',part.get('surface','generic'));metal=spec.get('metal',False) or surface=='metal' or 'screw' in role.lower() or 'nut' in role.lower() or role=='Standoffs'
    bs.inputs['Base Color'].default_value=(*( (.36,.36,.36) if clay else color),1)
    finish=surface_finish(surface,o['rough'],clay)
    bs.inputs['Roughness'].default_value=finish['roughness'];bs.inputs['Metallic'].default_value=0 if clay else (.72 if surface=='motor_bell' else .64 if metal else 0.)
    bs.inputs['Specular IOR Level'].default_value=finish['specular']
    bs.inputs['Coat Weight'].default_value=finish['coat'];bs.inputs['Coat Roughness'].default_value=finish['coat_roughness']
    if finish['bump']:
        # Millimetre-scale soft polymer grain, no geometry or colour change.
        coord=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value=1800.;noise.inputs['Detail'].default_value=2.
        links.new(coord.outputs['Object'],noise.inputs['Vector'])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=finish['bump'];bump.inputs['Distance'].default_value=.000045
        links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    if not clay and kind!='plain' and data['texture_opacity']>0:
        img=n.new('ShaderNodeTexImage');img.image=bpy.data.images.load(data['texture'] if kind=='weave' else data['edge_texture'],check_existing=True);img.extension='REPEAT'
        uv=n.new('ShaderNodeTexCoord');links.new(uv.outputs['UV'],img.inputs['Vector']);mix=n.new('ShaderNodeMixRGB');mix.inputs[0].default_value=data['texture_opacity'];mix.inputs[1].default_value=(*color,1);links.new(img.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Base Color'])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12*data['texture_opacity'];bump.inputs['Distance'].default_value=.00008;links.new(img.outputs['Color'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    if not clay:
        optics=part.get('optics')
        if surface=='prop' and optics:
            bs.inputs['IOR'].default_value=optics['ior']
            bs.inputs['Transmission Weight'].default_value=optics['transmission']
            bs.inputs['Roughness'].default_value=min(.98,optics['roughness']*o['rough'])
        elif part['alpha']<.99:
            # Viewport reference transparency approximated as transmission, not missing geometry.
            bs.inputs['Transmission Weight'].default_value=min(.65,1-part['alpha'])
    return m

material_cache={}
def shared_material(part,spec):
    role=part['role'].lower()
    hardware=('screw' in role or 'nut' in role or role=='standoffs')
    key=(spec.get('surface',part.get('surface','generic')),spec['kind'],tuple(spec['color']),bool(spec.get('metal',False)),hardware,part['alpha'],tuple(sorted((part.get('optics') or {}).items())))
    if key not in material_cache:material_cache[key]=material(part,spec)
    return material_cache[key]

vertices=[];subject_objects=[]
for part in data['parts']:
    mesh=bpy.data.meshes.new(part['name']);mesh.from_pydata(part['vertices'],[],part['triangles']);mesh.update();obj=bpy.data.objects.new(part['name'],mesh);scene.collection.objects.link(obj);subject_objects.append(obj)
    for spec in part['materials']:mesh.materials.append(shared_material(part,spec))
    textured=o['style']!=3 and data['texture_opacity']>0 and any(m['kind']!='plain' for m in part['materials'])
    uv=mesh.uv_layers.new(name='RotorForge UV') if textured else None;ca,sa=math.cos(part['angle']),math.sin(part['angle']);tile=max(.008,data['tile'])
    for poly,(mat,smooth) in zip(mesh.polygons,part['groups']):
        poly.material_index=mat;poly.use_smooth=smooth
        kind=part['materials'][mat]['kind']
        if uv is None or kind=='plain':continue
        for li in poly.loop_indices:
            x,y,z=mesh.vertices[mesh.loops[li].vertex_index].co
            if kind=='edge':u,v=((x if abs(poly.normal.y)>.7 else y) if not part['side'] else z), y if part['side'] else z;uv.data[li].uv=(u/.018,v/.002)
            else:
                u,v=(x,z) if part['side'] else (x,y);uv.data[li].uv=((ca*u+sa*v)/tile,(-sa*u+ca*v)/tile)
    vertices.extend(Vector(v) for v in part['vertices'])
# Render-only spinning prop representation. The annular meshes are lightweight
# and their shaders use angular/radial exposure coverage, not solid discs.
def prop_mesh(name, verts, faces, mat, uvs=None):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob);subject_objects.append(ob);mesh.materials.append(mat)
    if uvs is not None:
        uv=mesh.uv_layers.new(name='Spin UV')
        for poly,coords in zip(mesh.polygons,uvs):
            for li,coord in zip(poly.loop_indices,coords):uv.data[li].uv=coord
    vertices.extend(Vector(v) for v in verts)
    return ob


def prop_blur_material(prop):
    color=tuple(lin(max(0,min(1,c))) for c in prop['color'])
    if o['style']==3:color=(.36,.36,.36)
    m=bpy.data.materials.new('Spinning propeller — exposure coverage');m.use_nodes=True
    n=m.node_tree.nodes;links=m.node_tree.links;n.clear()
    uv=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');links.new(uv.outputs['UV'],sep.inputs[0])
    radial=n.new('ShaderNodeValToRGB');links.new(sep.outputs['Y'],radial.inputs[0]);r=radial.color_ramp;r.interpolation='EASE'
    r.elements[0].position=0.;r.elements[0].color=(0,0,0,1);r.elements[1].position=1.;r.elements[1].color=(0,0,0,1)
    for t,v in ((.10,.26),(.42,.85),(.69,1.),(.91,.35),(.975,.08)):
        r.elements.new(t).color=(v,v,v,1)
    coverage,ghost,streak=blur_profile(o['blur'])
    def mathnode(op,a,b=None):
        node=n.new('ShaderNodeMath');node.operation=op
        for index,value in enumerate((a,b)):
            if value is None:continue
            if isinstance(value,(int,float)):node.inputs[index].default_value=value
            else:links.new(value,node.inputs[index])
        return node.outputs[0]
    # Broad rapidly disappearing blade hints plus very faint fine radial streaks.
    theta=mathnode('MULTIPLY',sep.outputs['X'],math.tau)
    broad=mathnode('POWER',mathnode('MAXIMUM',mathnode('COSINE',mathnode('MULTIPLY',theta,3.)),0.),5.)
    fine=mathnode('POWER',mathnode('MAXIMUM',mathnode('COSINE',mathnode('MULTIPLY',theta,48.)),0.),4.)
    opacity=mathnode('MULTIPLY',radial.outputs['Color'],mathnode('ADD',coverage,mathnode('ADD',mathnode('MULTIPLY',broad,ghost),mathnode('MULTIPLY',fine,streak*.09))))
    opacity=mathnode('MULTIPLY',opacity,.48+.52*prop['alpha'])
    clear=n.new('ShaderNodeBsdfTransparent');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.34
    bs.inputs['Specular IOR Level'].default_value=.24
    mix=n.new('ShaderNodeMixShader');links.new(opacity,mix.inputs[0]);links.new(clear.outputs[0],mix.inputs[1]);links.new(bs.outputs[0],mix.inputs[2]);out=n.new('ShaderNodeOutputMaterial');links.new(mix.outputs[0],out.inputs['Surface'])
    return m


def spinning_prop(prop,index,blur_mat,hub_mat):
    x,y,z=prop['center'];radius=prop['radius'];hub=prop['hub'];steps=144
    # Use a ring with a UV seam; angular variation wraps exactly at both ends.
    verts=[];faces=[];uvs=[]
    for r in (hub*.90,radius):
        verts.extend((x+r*math.cos(math.tau*i/steps),y+r*math.sin(math.tau*i/steps),z) for i in range(steps))
    for i in range(steps):
        j=(i+1)%steps;faces.append((i,steps+i,steps+j,j));u=i/steps;v=(i+1)/steps
        uvs.append(((u,0),(u,1),(v,1),(v,0)))
    prop_mesh('Spinning propeller %d'%(index+1),verts,faces,blur_mat,uvs)
    if not prop['detailed']:return
    # Retain a sharp annular hub at the actual motor position and prop height.
    count=48;half=prop['hub_height']/2;verts=[];faces=[]
    for level,r in ((z-half,hub),(z+half,hub),(z+half,prop['bore']),(z-half,prop['bore'])):
        verts.extend((x+r*math.cos(math.tau*i/count),y+r*math.sin(math.tau*i/count),level) for i in range(count))
    for ring in range(4):
        next_ring=(ring+1)%4
        for i in range(count):
            j=(i+1)%count;faces.append((ring*count+i,ring*count+j,next_ring*count+j,next_ring*count+i))
    hub_obj=prop_mesh('Propeller hub %d'%(index+1),verts,faces,hub_mat)
    for poly in hub_obj.data.polygons:poly.use_smooth=abs(poly.normal.z)<.5

props=data.get('propellers',[])
if props:
    prop=props[0];blur_mat=prop_blur_material(prop)
    part=dict(name='Propeller hub',role='PropellerDiscs',alpha=prop['alpha'],surface='prop',optics=prop['optics'])
    hub_mat=shared_material(part,dict(kind='plain',color=prop['color'],surface='prop'))
    for i,prop in enumerate(props):spinning_prop(prop,i,blur_mat,hub_mat)
if not vertices:raise RuntimeError('Empty render scene')
def bounds(vertices):
    lo=Vector(tuple(min(v[i] for v in vertices) for i in range(3)));hi=Vector(tuple(max(v[i] for v in vertices) for i in range(3)))
    return lo,hi
lo,hi=bounds(vertices);center=(lo+hi)/2;forward=Vector((0,1,0))
flying=o.get('flying',False)
if flying:
    # Local +Y is the nose. Positive user pitch means nose down; roll is
    # around the longitudinal Y axis. Apply to the entire render assembly.
    pitch=Matrix.Rotation(-math.radians(o.get('pitch',0)),4,'X')
    roll=Matrix.Rotation(math.radians(o.get('roll',0)),4,'Y')
    yaw=Matrix.Rotation(math.radians(o.get('yaw',0)),4,'Z')
    attitude=yaw@roll@pitch
    transform=Matrix.Translation(center)@attitude@Matrix.Translation(-center)
    for ob in subject_objects:ob.matrix_world=transform@ob.matrix_world
    vertices=[transform@v for v in vertices];forward=attitude.to_3x3()@forward
    lo,hi=bounds(vertices);center=(lo+hi)/2
size=max(max(hi-lo),.01)
ey=Vector(o['eye']).normalized();up=Vector(o['up']).normalized();right=up.cross(ey).normalized();up=ey.cross(right).normalized()
rotation=Matrix((right,up,ey)).transposed().to_quaternion();cam_data=bpy.data.cameras.new('Studio Camera');cam=bpy.data.objects.new('Studio Camera',cam_data);scene.collection.objects.link(cam);scene.camera=cam;cam.rotation_mode='QUATERNION';cam.rotation_quaternion=rotation;cam_data.lens=o['lens'];cam_data.clip_start=.001;cam_data.clip_end=100;cam_data.dof.use_dof=False
# Use Blender's real camera frustum (including sensor fit and render aspect).
cam_data.sensor_fit='HORIZONTAL';cam_data.type='ORTHO' if o['orthographic'] else 'PERSP';cam_data.ortho_scale=1.
def frame_extents():
    frame=cam_data.view_frame(scene=scene)
    coords=[(v.x,v.y) if o['orthographic'] else (v.x/-v.z,v.y/-v.z) for v in frame]
    x,y=zip(*coords);return (min(x),max(x),min(y),max(y))
viewport=o.get('viewport')
if viewport is not None:
    # Copy the real FreeCAD camera, not just its orientation. Keep the same
    # optical centre and widen the frustum only when framing requires it.
    cam.location=Vector(viewport['position']);cam_data.shift_x=cam_data.shift_y=0.
    aspect=o['width']/o['height']
    half=viewport_half_height(viewport['extent'],viewport['aspect'],aspect,o['orthographic'],o['zoom'])
    points=[((v-cam.location).dot(right),(v-cam.location).dot(up),-(v-cam.location).dot(ey)) for v in vertices]
    half=viewport_safe_half_height(points,aspect,half,o['orthographic'])
    a,b,c,d=frame_extents();actual=(d-c)/2
    if o['orthographic']:cam_data.ortho_scale*=half/actual
    else:cam_data.lens*=actual/half
    print('RotorForge matched FreeCAD camera:',cam_data.type,'lens',cam_data.lens,'position',tuple(cam.location),flush=True)
else:
    a,b,c,d=frame_extents();half_x=(b-a)/2;half_y=(d-c)/2
    points=[((v-center).dot(right),(v-center).dot(up),(v-center).dot(ey)) for v in vertices]
    zoom,bias_x,bias_y=flight_margins(o['zoom'],o.get('flight_bias',0.) if flying else 0.,forward.dot(right),forward.dot(up))
    cx,cy,distance,ortho_scale,sx,sy=fit_camera(points,half_x,half_y,zoom,o['orthographic'])
    cam.location=center+right*cx+up*cy+ey*distance
    if o['orthographic']:
        cam_data.ortho_scale=ortho_scale
        cam.location+=right*(2*half_x*ortho_scale*bias_x)+up*(2*half_y*ortho_scale*bias_y)
    else:
        # Calibrate the lens shift against Blender's own camera-frame convention.
        # Positioning the view on the projected mesh bounds removes unequal top/bottom margins.
        cam_data.shift_x=1.;a1,b1,_,_=frame_extents();cam_data.shift_x=0.
        cam_data.shift_y=1.;_,_,c1,d1=frame_extents();cam_data.shift_y=0.
        sx+=2*half_x*bias_x;sy+=2*half_y*bias_y
        cam_data.shift_x=(sx-(a+b)/2)/((a1+b1-a-b)/2)
        cam_data.shift_y=(sy-(c+d)/2)/((c1+d1-c-d)/2)
del points,vertices
style=o['style'];look=lighting_settings(style,o.get('lighting'));bg=look['bg'];floor=look['floor']
if o['background']==2:bg=(.85,.85,.85);floor=(.78,.78,.78)
if o['background']==3:bg=(.002,.002,.002);floor=(.006,.006,.006)
# Separate the photographed backdrop from the world light. A dark backdrop
# no longer needs a bright world just to make the model visible.
scene.world.use_nodes=True;nodes=scene.world.node_tree.nodes;links=scene.world.node_tree.links;nodes.clear()
world=nodes.new('ShaderNodeBackground');world.inputs['Color'].default_value=(*look['ambient'],1);world.inputs['Strength'].default_value=o['world']
backdrop=nodes.new('ShaderNodeBackground');backdrop.inputs['Color'].default_value=(*bg,1);backdrop.inputs['Strength'].default_value=1.
ray=nodes.new('ShaderNodeLightPath');mix=nodes.new('ShaderNodeMixShader');out=nodes.new('ShaderNodeOutputWorld')
links.new(ray.outputs['Is Camera Ray'],mix.inputs[0]);links.new(world.outputs[0],mix.inputs[1]);links.new(backdrop.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
scene.render.film_transparent=o['background']==1
if props:scene.cycles.transparent_max_bounces=max(8,scene.cycles.transparent_max_bounces)
if o['floor'] and not scene.render.film_transparent and (not flying or o.get('flight_shadow',True)):
    floor_z=lo.z-(size*o.get('flight_height',.26) if flying else .0005)
    floor_origin=(center.x,center.y,floor_z)
    bpy.ops.mesh.primitive_plane_add(size=size*200,location=floor_origin)
    plane=bpy.context.object;m=bpy.data.materials.new('Seamless studio floor');m.use_nodes=True
    n=m.node_tree.nodes;links=m.node_tree.links;bs=n.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*floor,1);bs.inputs['Roughness'].default_value=o['ground_rough'];bs.inputs['Specular IOR Level'].default_value=.13
    # A camera-only, smooth radial fade makes the distant floor converge to
    # the exact same linear color as the visible world. Avoid volume fog,
    # which would wash out the subject, add noise and slow Cycles rendering.
    # Keep the physical floor (including contact shadows/reflections) intact
    # near the subject and on indirect light paths.
    geom=n.new('ShaderNodeNewGeometry');dist=n.new('ShaderNodeVectorMath');dist.operation='DISTANCE'
    links.new(geom.outputs['Position'],dist.inputs[0]);dist.inputs[1].default_value=floor_origin
    fade=n.new('ShaderNodeMapRange');fade.interpolation_type='SMOOTHERSTEP';fade.clamp=True
    links.new(dist.outputs['Value'],fade.inputs['Value'])
    fade.inputs['From Min'].default_value=size*2.5;fade.inputs['From Max'].default_value=size*12.
    fade.inputs['To Min'].default_value=0.;fade.inputs['To Max'].default_value=1.
    camera_ray=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY'
    links.new(fade.outputs['Result'],weight.inputs[0]);links.new(camera_ray.outputs['Is Camera Ray'],weight.inputs[1])
    distant=n.new('ShaderNodeEmission');distant.inputs['Color'].default_value=(*bg,1);distant.inputs['Strength'].default_value=1.
    blend=n.new('ShaderNodeMixShader');links.new(weight.outputs[0],blend.inputs[0]);links.new(bs.outputs[0],blend.inputs[1]);links.new(distant.outputs[0],blend.inputs[2])
    links.new(blend.outputs[0],n.get('Material Output').inputs['Surface']);plane.data.materials.append(m)
# Lights follow the camera azimuth, not the arbitrary global XY direction.
front=Vector((ey.x,ey.y,0))
if front.length<1e-6:front=Vector((-up.x,-up.y,0))
front.normalize();side=front.cross(Vector((0,0,1))).normalized();vertical=Vector((0,0,1))
def area(name,rig,power,color):
    if power<=0:return
    direction,width,height=rig
    l=bpy.data.lights.new(name,'AREA');l.energy=area_power(style,size,power);l.color=color
    l.shape='DISK' if height is None else 'RECTANGLE';l.size=size*width*o['soft']
    if height is not None:l.size_y=size*height*o['soft']
    ob=bpy.data.objects.new(name,l);scene.collection.objects.link(ob)
    ob.location=center+(side*direction[0]+front*direction[1]+vertical*direction[2])*size
    ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
for name,rig,power,color in zip(('Key','Fill','Rim','Accent'),LIGHT_RIGS[look['rig']],
                                (o['key'],o['fill'],o['rim'],look['accent']),
                                (look['key_color'],look['fill_color'],look['rim_color'],look['accent_color'])):
    area(name,rig,power,color)
# A subtle front-balance light preserves the intended mood but prevents some
# creative presets from making the nose noticeably darker than the rear.
front_balance=max(0., min(1., float(look.get('front_balance', .16))))
if front_balance>0:
    # Increase slightly when the preset relies heavily on rim lighting.
    power=front_balance*(0.75 + 0.35*max(0., o['rim']-o['fill']))
    area('Front balance',((-.10,1.45,.95),1.85,1.10),power,look['key_color'])
# AgX preserves highlight detail; correct lighting before tone mapping.
scene.view_settings.view_transform='AgX'
try:scene.view_settings.look=look['look']
except (ValueError,TypeError):pass
scene.view_settings.exposure=o['exposure'];scene.render.resolution_x=o['width'];scene.render.resolution_y=o['height'];scene.render.resolution_percentage=100;scene.render.image_settings.file_format='JPEG' if Path(output).suffix.lower() in ('.jpg','.jpeg') else 'PNG';scene.render.image_settings.color_mode='RGBA' if scene.render.film_transparent else 'RGB';scene.render.filepath=output;scene.render.use_file_extension=False
# Lossless PNG preserves details and alpha; retain more tonal precision for finals.
if scene.render.image_settings.file_format=='PNG':
    scene.render.image_settings.color_depth='8' if o.get('preview',False) else '16'
else:scene.render.image_settings.quality=100
bpy.ops.render.render(write_still=True)
