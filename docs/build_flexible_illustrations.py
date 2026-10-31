"""Render exact exported FreeCAD meshes on light backgrounds for the Help."""
from pathlib import Path
import json,sys,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
ROOT=Path(__file__).resolve().parents[1];source=Path(sys.argv[1])
COLORS={'TopPlate':'#4d7fa5','MidPlate':'#6592b0','BottomPlate':'#4d7fa5','ElectronicsGuardLeft':'#50a4af','ElectronicsGuardRight':'#50a4af','Metal posts':'#a6adb5','Carbon side plate':'#4d7fa5','Camera reference':'#bac7cf','Flexible interface':'#dcaa57','MotorProtectorFrontRight':'#50a4af'}
def scene(ax,parts):
 allpts=[]
 for part in parts:
  v=np.array(part['vertices']);faces=np.array(part['faces']);polys=v[faces];allpts.append(v)
  n=np.cross(polys[:,1]-polys[:,0],polys[:,2]-polys[:,0]);n/=np.maximum(1e-9,np.linalg.norm(n,axis=1))[:,None]
  color=np.array(matplotlib.colors.to_rgb(COLORS[part['role']]))
  shade=.56+.44*np.abs(n@np.array([.4,-.3,.866]));rgba=np.column_stack((shade[:,None]*color,np.ones(len(shade))))
  collection=Poly3DCollection(polys,facecolors=rgba,edgecolors='none',zsort='average');ax.add_collection3d(collection)
 v=np.concatenate(allpts);low=v.min(axis=0);high=v.max(axis=0);span=high-low;centre=(high+low)/2;radius=max(span)*.55
 for axis,c,d in zip(('x','y','z'),centre,span):getattr(ax,'set_'+axis+'lim')(c-max(d*.55,2),c+max(d*.55,2))
 ax.set_box_aspect(np.maximum(span,4),zoom=1.12);ax.set_proj_type('ortho');ax.view_init(elev=24,azim=55);ax.set_axis_off();ax.set_facecolor('white')
def render(name,filename,cols,width,height):
 scenes=json.loads((source/(name+'.json')).read_text());rows=(len(scenes)+cols-1)//cols
 fig=plt.figure(figsize=(width,height),facecolor='white');fig.subplots_adjust(left=0,right=1,bottom=.02,top=.92,wspace=.15 if name in ('vent_shapes','usb') else -.06,hspace=.15)
 for i,data in enumerate(scenes):
  if name in ('vent_shapes','usb'):
   from matplotlib.collections import PolyCollection
   ax=fig.add_subplot(rows,cols,i+1)
   for part in data['parts']:
    v=np.array(part['vertices']);faces=np.array(part['faces']);ax.add_collection(PolyCollection(v[faces][:,:,1:3],facecolors=COLORS[part['role']],edgecolors='none'))
   ax.autoscale_view();ax.set_aspect('equal');ax.margins(.08);ax.set_axis_off()
   if name=='vent_shapes':ax.set_xlim(-25,25);ax.set_ylim(26,34)
  elif 'loops' in data:
   from matplotlib.path import Path as PlotPath
   from matplotlib.patches import PathPatch
   ax=fig.add_subplot(rows,cols,i+1);paths=[]
   for index,loop in enumerate(data['loops']):
    pts=np.array(loop);area=np.sum(pts[:,0]*np.roll(pts[:,1],-1)-np.roll(pts[:,0],-1)*pts[:,1])
    if (area>0)!=(index==0):pts=pts[::-1]
    paths.append(PlotPath(pts,closed=True))
   ax.add_patch(PathPatch(PlotPath.make_compound_path(*paths),facecolor=COLORS[data['parts'][0]['role']],edgecolor='#345d6c',linewidth=.5))
   ax.autoscale_view();ax.set_aspect('equal');ax.margins(.1);ax.set_axis_off()
  else:
   ax=fig.add_subplot(rows,cols,i+1,projection='3d');scene(ax,data['parts'])
  ax.set_title(data['title'],fontfamily='DejaVu Sans',fontsize=14,color='#183542',pad=8)
  if name=='guards':ax.view_init(elev=24,azim=-55)
  if name=='grip_height':ax.view_init(elev=16,azim=160)
  if name=='service':ax.view_init(elev=-90,azim=-90)
  if name=='features' and 'loops' not in data:
   ax.view_init(elev=0 if i==1 else -90 if i==2 else 24,azim=0 if i==1 else -90 if i==2 else -55)
 fig.savefig(ROOT/'docs'/filename,dpi=190,facecolor='white');plt.close(fig)
if (source/'camera.json').exists():render('camera','FlexibleCameraModes.png',3,12,5.7)
if (source/'guards.json').exists():render('guards','ElectronicsGuards.png',1,8,5)
if (source/'vent_shapes.json').exists():render('vent_shapes','GuardVentShapes.png',2,12,7.5)
if (source/'usb.json').exists():render('usb','GuardUSBAccess.png',1,8,3.7)
if (source/'service.json').exists():render('service','MotorGuardService.png',2,10,4.5)
if (source/'arms.json').exists():render('arms','ArmFillets.png',2,10,5)
if (source/'features.json').exists():render('features','PrintableProtectionOverview.png',2,12,9)
print('Rendered native protection figures')

if (source/'grip_height.json').exists():render('grip_height','GuardGripHeight.png',1,8,5)
if (source/'grip_sections.json').exists():render('grip_sections','GuardGripSections.png',2,11,4.8)

# The catalogue follows the current enum, even when older native scene data
# contains only the original six profiles.
from build_guard_vent_catalogue import build_catalogue
build_catalogue()
