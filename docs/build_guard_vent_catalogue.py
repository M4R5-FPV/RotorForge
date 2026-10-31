"""Render all current side-guard vent profiles from shared portable geometry."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from freecad.rotorforge.flex_options import GUARD_VENT_SHAPES
from freecad.rotorforge.protection_layout import vent_polygon
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon,Ellipse,FancyBboxPatch
def build_catalogue():
 fig,axs=plt.subplots(4,4,figsize=(12,8.8),facecolor='white')
 for ax,name in zip(axs.flat,GUARD_VENT_SHAPES):
  ax.add_patch(FancyBboxPatch((-12,-5),24,10,boxstyle='round,pad=0,rounding_size=1',facecolor='#50a4af',edgecolor='#276a76',lw=.8))
  for y in ((0,) if name=='Horizontal slots' else (-6,6)):
   points=vent_polygon(dict(shape=name,width=8.,height=5.))
   if points:patch=Polygon([(y+x,z) for x,z in points],closed=True,facecolor='white',edgecolor='#276a76',lw=.6)
   elif name=='Ellipses':patch=Ellipse((y,0),8,5,facecolor='white',edgecolor='#276a76',lw=.6)
   elif name=='Rounded slots':patch=FancyBboxPatch((y-4,-2.5),8,5,boxstyle='round,pad=0,rounding_size=2.5',facecolor='white',edgecolor='#276a76',lw=.6)
   else:patch=Rectangle((y-10,-2.5),20,5,facecolor='white',edgecolor='#276a76',lw=.6)
   ax.add_patch(patch)
  ax.set_xlim(-13,13);ax.set_ylim(-6,6);ax.set_aspect('equal');ax.set_axis_off();ax.set_title(name,fontsize=11,color='#183542')
 fig.subplots_adjust(left=.02,right=.98,top=.95,bottom=.02,wspace=.13,hspace=.35)
 fig.savefig(ROOT/'docs/GuardVentShapes.png',dpi=180);plt.close(fig)

if __name__=='__main__':build_catalogue()
