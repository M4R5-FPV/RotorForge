"""Actual standoff rows used by the electronics side panels."""
def row_pair(stands,y):
 row=sorted((s for s in stands if abs(s['point'][1]-y)<1e-6),key=lambda s:s['point'][0])
 return (row[0],row[-1]) if len(row)>=2 else ()
def rear_pair(p):
 from .parameters import standoff_layouts
 stands=standoff_layouts(p)
 return row_pair(stands,min(s['point'][1] for s in stands))
def stack_pair(p):
 from .parameters import standoff_layouts
 stands=standoff_layouts(p);ry=rear_pair(p)[0]['point'][1]
 ys={s['point'][1] for s in stands if s['point'][1]>ry+1e-6}
 return row_pair(stands,min(ys,key=lambda y:(abs(y-p.StackOffsetY),y))) if ys else ()
def front_stack_pair(p):
 # Forward coverage must reach the actual foremost row, including an added
 # fourth pair that lies beyond the nominal front pair.
 from .parameters import standoff_layouts
 stands=standoff_layouts(p)
 return row_pair(stands,max(s['point'][1] for s in stands))
def rear_mount_seats(p):
 """Non-recursive stack: carrier, ELRS, guard bearing, VTX, top plate."""
 from .parameters import plate_levels
 pair=rear_pair(p);levels=plate_levels(p)
 base=max(levels['deck_z'],*(s['base'] for s in pair))
 ceiling=min(levels['top_z'],*(s['base']+s['length'] for s in pair))
 top=ceiling-(p.FlexAntennaTopGap if p.FlexRearAntenna else 0.)
 low=base+(p.FlexELRSHeightOffset if p.FlexELRSEnabled else 0.)
 vg=p.FlexAntennaGuardGap if p.FlexRearAntenna and p.FlexSideGuards else 0.
 eg=p.FlexELRSGuardGap if p.FlexELRSEnabled and p.FlexSideGuards else 0.
 guard=4. if p.FlexSideGuards else 0.
 elrs_space=max(0.,top-low-guard-vg-eg-(4. if p.FlexRearAntenna else 0.))
 eh=min(p.FlexELRSGripHeight,elrs_space) if p.FlexELRSEnabled else 0.
 vtx_space=max(0.,top-low-eh-guard-vg-eg)
 vh=min(p.FlexAntennaGripHeight,vtx_space) if p.FlexRearAntenna else 0.
 return dict(base=base,ceiling=ceiling,elrs_z=low,elrs_height=eh,elrs_space=elrs_space,
             vtx_z=top-vh,vtx_top=top,vtx_space=vtx_space,
             guard_low=low+eh+eg,guard_high=top-vh-vg)

def rear_guard_band(p):
 if p.FlexRearAntenna or p.FlexELRSEnabled:
  a=rear_mount_seats(p);return a['guard_low'],a['guard_high']
 s=rear_pair(p)[0];middle=s['base']+s['length']/2
 return middle-3,middle+3
