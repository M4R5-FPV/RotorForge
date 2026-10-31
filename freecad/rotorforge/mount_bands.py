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
def rear_guard_band(p):
 s=rear_pair(p)[0];middle=s['base']+s['length']/2
 return middle-3,middle+3
