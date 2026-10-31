"""Non-destructive, validity-checked CAD face cleanup; no FreeCAD imports."""
def guard_refine(shape):
 """Keep the valid boolean when OCC face unification damages its topology.
 Removing splitter edges is cosmetic: it must not invalidate a connected guard
 or change its solid count. Coincident plate-height lips and sleeve faces can
 trigger this in supported OCC versions, especially at zero plate clearance.
 """
 try:
  refined=shape.copy().removeSplitter()
  if refined.isValid() and len(refined.Solids)==len(shape.Solids):
   return refined
 except Exception:
  pass
 return shape

