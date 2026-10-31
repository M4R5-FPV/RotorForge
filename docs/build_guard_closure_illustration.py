"""Render the closure_scene.json exported by tests/freecad_revision066.py."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
parts=json.loads(Path(sys.argv[1]).read_text())
fig=plt.figure(figsize=(11,5.7),facecolor='white');ax=fig.add_subplot(111,projection='3d');allpts=[]
for part in parts:
 v=np.array(part['vertices']);polys=v[np.array(part['faces'])];allpts.append(v)
 n=np.cross(polys[:,1]-polys[:,0],polys[:,2]-polys[:,0]);n/=np.maximum(1e-9,np.linalg.norm(n,axis=1))[:,None]
 base=np.array(matplotlib.colors.to_rgb('#50a4af' if part['role'].startswith('Electronics') else '#6592b0' if part['role']=='MidPlate' else '#4d7fa5'))
 shade=.72+.28*np.abs(n@np.array([.4,-.3,.866]));ax.add_collection3d(Poly3DCollection(polys,facecolors=shade[:,None]*base,edgecolors='none',zsort='average'))
v=np.concatenate(allpts);low=v.min(axis=0);high=v.max(axis=0);span=high-low;centre=(high+low)/2
for axis,c,d in zip('xyz',centre,span):getattr(ax,'set_'+axis+'lim')(c-max(d*.53,2),c+max(d*.53,2))
ax.set_box_aspect(span,zoom=1.13);ax.set_proj_type('ortho');ax.view_init(elev=24,azim=145);ax.set_axis_off();ax.set_facecolor('white')
fig.subplots_adjust(left=0,right=1,bottom=0,top=1)
fig.savefig(ROOT/'docs/GuardFrontClosure.png',dpi=200,facecolor='white');plt.close(fig)
