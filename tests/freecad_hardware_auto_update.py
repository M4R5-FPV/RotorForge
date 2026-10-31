"""GUI regression: edits keep selected fasteners current without hiding/recreation."""
import os,sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,FreeCADGui as Gui
from freecad.rotorforge import document as d,hardware_refs as hw
from freecad.rotorforge.parameters import Parameters
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
checks=[];failures=[]
try:
 Gui.showMainWindow()
 doc=App.newDocument();p=Parameters(StackPressNuts=True)
 frame=d.create_frame(p,doc)
 hw.options(frame)
 q=replace(p,RootBoltSpacing=9.)
 d.update_frame(frame,q);assert not hw.objects(frame)
 checks.append('Opening settings alone does not enable references')
 hw.refresh(frame,dict(groups=['Stack hardware'],nuts=False,engagement=3.))
 refs=hw.objects(frame);assert len(refs)==1 and refs[0].ViewObject.Visibility
 obj=refs[0];name=obj.Name
 assert len(obj.Shape.Solids)==12 # 4 headed screws, 4 upper nuts, 4 press nuts
 class Observer:
  def __init__(self):self.writes=[]
  def slotChangedObject(self,o,prop):
   if o.Name==name and prop=='Shape':self.writes.append(prop)
 observer=Observer();App.addDocumentObserver(observer)
 old=obj.Shape.copy();signature=obj.HardwareSignature
 original_screw=hw.screw
 def no_build(*args):raise AssertionError('Unchanged reference geometry was rebuilt')
 hw.screw=no_build
 q=replace(q,TopLength=q.TopLength+1.)
 d.update_frame(frame,q)
 assert hw.objects(frame)[0].Name==name and obj.ViewObject.Visibility
 assert obj.HardwareSignature==signature and abs(obj.Shape.Volume-old.Volume)<1e-7
 assert not hw.settings(frame).ReferencesStale
 hw.screw=original_screw
 checks.append('Unrelated edit keeps object, visibility and shape without fastener rebuilds')
 before=obj.Shape.BoundBox.ZMax
 q=replace(q,StackHeight=q.StackHeight+1.)
 d.update_frame(frame,q)
 assert hw.objects(frame)[0].Name==name and obj.ViewObject.Visibility and observer.writes
 assert abs(obj.Shape.BoundBox.ZMax-before-1.)<1e-5
 assert hw.options(frame)['groups']==['Stack hardware']
 checks.append('Stack nuts automatically follow changed height with group selection preserved')
 hw.set_visible(frame,False)
 q=replace(q,StackHeight=q.StackHeight-.5);d.update_frame(frame,q)
 assert not obj.ViewObject.Visibility
 hw.set_visible(frame,True);hw.sync_refs(frame);assert obj.ViewObject.Visibility
 checks.append('Explicit Hide remains hidden through updates')
 # Exercise paused references on an invalid direct property edit, then recovery.
 frame.StackHeight=100.;doc.recompute()
 assert str(frame.Status).startswith('Invalid') and not obj.ViewObject.Visibility
 hw.set_visible(frame,True);assert not obj.ViewObject.Visibility
 frame.StackHeight=q.StackHeight;doc.recompute()
 assert str(frame.Status).startswith('Valid') and obj.ViewObject.Visibility
 checks.append('Invalid edits pause references; valid recovery restores visibility')
 App.removeDocumentObserver(observer)
 # Simulate pre-fix metadata and retain the existing object on migration.
 obj=hw.objects(frame)[0];name=obj.Name;t=hw.settings(frame)
 for prop in ('ReferencesCreated','ReferencesVisible','ReferencesStale'):t.removeProperty(prop)
 for prop in ('HardwareRole','HardwareSignature','HardwareVisible'):obj.removeProperty(prop)
 t.SourceSignature='Current'
 q=replace(q,StackHeight=q.StackHeight-.25);d.update_frame(frame,q)
 assert len(hw.objects(frame))==1 and hw.objects(frame)[0].Name==name and obj.ViewObject.Visibility
 checks.append('Pre-fix saved hardware upgrades in place')
 # Old versions hid references automatically and marked this exact state.
 for prop in ('ReferencesCreated','ReferencesVisible','ReferencesStale'):t.removeProperty(prop)
 obj.removeProperty('HardwareVisible');obj.ViewObject.Visibility=False
 t.SourceSignature='Refresh hardware after changing the frame.'
 q=replace(q,StackHeight=q.StackHeight+.1);d.update_frame(frame,q)
 assert obj.ViewObject.Visibility and not t.ReferencesStale
 checks.append('Old automatically hidden references recover on update')
 # Arm press nuts follow edits too, without replacing their document nodes.
 q=replace(q,ArmNutMount='M3 press nut');d.update_frame(frame,q)
 hw.refresh(frame,dict(groups=['Arm bolts','Stack hardware'],nuts=True,engagement=3.))
 names={o.HardwareRole:o.Name for o in hw.objects(frame)}
 q=replace(q,RootBoltSpacing=9.2);d.update_frame(frame,q)
 assert {o.HardwareRole:o.Name for o in hw.objects(frame)}==names
 for o in hw.objects(frame):
  assert o.ViewObject.Visibility and o.Shape.isValid()
  if o.HardwareRole.startswith('Arm'):assert len(o.Shape.Solids)==4
 checks.append('Arm press nuts follow bolt edits without replacing references')
 path=out/'AutoHardware.FCStd';doc.saveAs(str(path))
except Exception:
 failures.append(traceback.format_exc());traceback.print_exc()
(out/'hardware_auto.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2))
print('RESULT',checks,failures,flush=True)
os._exit(1 if failures else 0)
