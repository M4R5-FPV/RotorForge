"""Portable opt-in antenna-reference tests; no FreeCAD GUI or OpenCASCADE required."""
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from dataclasses import replace
from unittest.mock import patch

from freecad.rotorforge.parameters import Parameters, require_valid, save_parameters, load_parameters
from freecad.rotorforge.editor_sections import FIELD_LOCATION
from freecad.rotorforge.appearance import design_signature
from freecad.rotorforge.antenna_layout import antenna_layout
from freecad.rotorforge.elrs_layout import elrs_layout
from freecad.rotorforge.antenna_preset_specs import vtx_spec,elrs_spec,elrs_feed_to_vtx,VTX_PRESETS,ELRS_SPAN_PRESETS,ELRS_FEED_PRESETS


class Vector:
    def __init__(self,x,y=None,z=None):
        if y is None:x,y,z=x
        self.x,self.y,self.z=float(x),float(y),float(z)
    def __add__(self,other):return Vector(self.x+other.x,self.y+other.y,self.z+other.z)
    def __sub__(self,other):return Vector(self.x-other.x,self.y-other.y,self.z-other.z)
    def __mul__(self,scalar):return Vector(self.x*scalar,self.y*scalar,self.z*scalar)
    __rmul__=__mul__


class Primitive:
    def __init__(self,kind,*args):self.kind,self.args=kind,args;self.Faces=[object()]


class Part:
    @staticmethod
    def Shape():return Primitive('null')
    @staticmethod
    def makeCylinder(r,h,p,d):return Primitive('cylinder',r,h,p,d)
    @staticmethod
    def makeSphere(r,p):return Primitive('sphere',r,p)
    @staticmethod
    def makeBox(dx,dy,dz,p):return Primitive('box',dx,dy,dz,p)
    @staticmethod
    def makeCone(r1,r2,h,p,d):return Primitive('cone',r1,r2,h,p,d)
    @staticmethod
    def makeCompound(items):
        obj=Primitive('compound',items)
        obj.Faces=[f for part in items for f in part.Faces]
        return obj


def load_reference_module():
    """Load only the model file against an instrumented Part backend."""
    name='freecad.rotorforge._test_antenna_reference_models'
    path=Path(__file__).resolve().parents[1]/'freecad/rotorforge/antenna_reference_models.py'
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules,{'FreeCAD':types.SimpleNamespace(Vector=Vector),'Part':Part}):
        spec.loader.exec_module(mod)
    return mod


class AntennaReferenceTests(unittest.TestCase):
    def test_controls_are_opt_in_and_visible_in_finishing(self):
        p=Parameters()
        for key in ('ShowVTXAntennaReference','ShowELRSTReference'):
            self.assertFalse(getattr(p,key))
            self.assertEqual(FIELD_LOCATION[key][0],'Finishing')
        self.assertTrue(p.ShowReferences)

    def test_invalid_dimensions_block_opted_in_reference(self):
        base=Parameters()
        with self.assertRaisesRegex(ValueError,'VTX antenna reference length'):
            require_valid(replace(base,FlexRearAntenna=True,ShowVTXAntennaReference=True,VTXAntennaReferenceLength=1.0))
        with self.assertRaisesRegex(ValueError,'ELRS T-antenna span'):
            require_valid(replace(base,FlexELRSEnabled=True,ShowELRSTReference=True,ELRSTReferencePreset='Custom',ELRSTReferenceSpan=10.0))

    def test_vtx_count_pose_and_display_colours(self):
        model=load_reference_module()
        p=replace(Parameters(),FlexRearAntenna=True,ShowVTXAntennaReference=True,
                  FlexAntennaCount='2 antennas',FlexAntennaTilt=40.)
        shape,colours=model.antenna_reference(p,'VTXAntennaReference')
        self.assertEqual(len(colours),len(shape.Faces))
        # Slim cable, small boot, head flare, short shell, rounded crown, collar.
        self.assertEqual(len(shape.args[0]),12)
        holders=antenna_layout(p)['holders']
        cylinders=[item for item in shape.args[0] if item.kind=='cylinder']
        self.assertEqual(len(cylinders),8)
        self.assertAlmostEqual(cylinders[0].args[-1].z,holders[0]['axis'][2])
        self.assertAlmostEqual(cylinders[4].args[-1].z,holders[1]['axis'][2])
        self.assertNotEqual(holders[0]['axis'][0],holders[1]['axis'][0])
        spec=vtx_spec(p)
        cable=cylinders[0]
        self.assertLess(cable.args[0],spec['head_diameter']/5.)
        self.assertAlmostEqual(cable.args[1],spec['length']-spec['head_length'])
        self.assertTrue(any(x.kind=='cone' for x in shape.args[0]))
        self.assertTrue(model.reference_enabled(p,'VTXAntennaReference'))
        self.assertFalse(model.reference_enabled(replace(p,ShowReferences=False),'VTXAntennaReference'))

    def test_vtx_presets_have_slim_stem_and_short_radome(self):
        model=load_reference_module()
        for name in VTX_PRESETS:
            if name=='Custom':continue
            with self.subTest(preset=name):
                p=replace(Parameters(),FlexRearAntenna=True,ShowVTXAntennaReference=True,
                          VTXAntennaReferencePreset=name)
                spec=vtx_spec(p)
                shape,colours=model.antenna_reference(p,'VTXAntennaReference')
                cable=shape.args[0][0]
                self.assertEqual(cable.kind,'cylinder')
                self.assertGreater(cable.args[1],spec['head_length']*1.5)
                self.assertLess(cable.args[0]*2,spec['head_diameter'])
                self.assertEqual(len(shape.Faces),len(colours))
        self.assertEqual(vtx_spec(replace(Parameters(),VTXAntennaReferencePreset='Avatar V2 105 mm'))['head_diameter'],15.)

    def test_elrs_t_span_and_feed_follow_hooks(self):
        model=load_reference_module()
        p=replace(Parameters(),FPVEnabled=True,VTXOffsetY=15.,VTXLength=36.,
                  FlexELRSEnabled=True,ShowELRSTReference=True,
                  FlexELRSHookReach=9.,ELRSTReferencePreset='Custom',ELRSTReferenceSpan=82.,
                  ELRSTReferenceFeedPreset='Custom',ELRSTReferenceStemLength=85.)
        shape,colours=model.antenna_reference(p,'ELRSTReference')
        self.assertEqual(len(colours),len(shape.Faces))
        layout=elrs_layout(p)
        items=shape.args[0]
        primary=items[0]
        self.assertAlmostEqual(primary.args[1],p.ELRSTReferenceSpan-p.FlexELRSAntennaDiameter)
        self.assertAlmostEqual(primary.args[2].y,layout['y'])
        self.assertAlmostEqual(primary.args[2].z,layout['z'])
        self.assertEqual(items[3].kind,'box')
        feed=items[4]
        expected=elrs_feed_to_vtx(p,feed.args[2].y)
        self.assertAlmostEqual(feed.args[1],expected)
        self.assertAlmostEqual(feed.args[2].y+feed.args[1],p.VTXOffsetY-p.VTXLength/2.-3.)
        self.assertEqual(feed.args[-1].y,1.0)
        self.assertTrue(model.reference_enabled(p,'ELRSTReference'))
        for preset,span in ELRS_SPAN_PRESETS.items():
            if span is not None:
                self.assertAlmostEqual(elrs_spec(replace(p,ELRSTReferencePreset=preset))['span'],span)
        for preset,length in ELRS_FEED_PRESETS.items():
            if length is not None:
                self.assertAlmostEqual(elrs_spec(replace(p,ELRSTReferenceFeedPreset=preset))['feed_length'],length)

    def test_elrs_feed_never_reaches_vtx_and_ignores_legacy_feed_settings(self):
        model=load_reference_module()
        p=replace(Parameters(),FPVEnabled=True,FlexELRSEnabled=True,ShowELRSTReference=True,
                  VTXOffsetY=35.,VTXLength=24.)
        for offset in (-120.,-65.,-20.,35.,70.):
            for old_feed in (0.,40.,95.,200.):
                current=replace(p,VTXOffsetY=offset,ELRSTReferenceFeedPreset='Custom',
                                ELRSTReferenceStemLength=old_feed)
                shape,colours=model.antenna_reference(current,'ELRSTReference')
                items=shape.args[0]
                leads=[v for v in items if v.kind=='cylinder' and v.args[-1].y==1.]
                self.assertEqual(len(leads),int(elrs_feed_to_vtx(current,
                      elrs_layout(current)['y']+max(3.5,min(5.5,current.FlexELRSAntennaDiameter))/2.)>.01))
                for lead in leads:
                    end_y=lead.args[2].y+lead.args[1]
                    self.assertLessEqual(end_y+3.,current.VTXOffsetY-current.VTXLength/2.+1e-8)
                    self.assertGreaterEqual(lead.args[1],0.)
                self.assertEqual(len(colours),len(shape.Faces))
        # The visual stem becomes absent if the T centre is already within the
        # nominal VTX rear boundary; the complete T crossbar remains visible.
        p2=replace(p,VTXOffsetY=-80.)
        shape,_=model.antenna_reference(p2,'ELRSTReference')
        self.assertEqual(len(shape.args[0]),4)

    def test_vtx_head_finish_is_independent_from_black_coax_and_elrs_dark(self):
        model=load_reference_module()
        chosen=[]
        for name,colour in model.VTX_HEAD_COLOURS.items():
            p=replace(Parameters(),FlexRearAntenna=True,ShowVTXAntennaReference=True,
                      VTXAntennaHeadColour=name)
            shape,face_colours=model.antenna_reference(p,'VTXAntennaReference')
            self.assertEqual(len(face_colours),len(shape.Faces))
            self.assertEqual(face_colours[0],model.COAX_COLOUR)
            self.assertIn(colour,face_colours)
            self.assertIn(model.RING,face_colours)
            chosen.append(colour)
        self.assertEqual(len(set(chosen)),6)
        self.assertEqual(design_signature(replace(Parameters(),VTXAntennaHeadColour='Red')),design_signature(Parameters()))
        elrs,_=model.antenna_reference(replace(Parameters(),FlexELRSEnabled=True,
                   ShowELRSTReference=True),'ELRSTReference')
        self.assertEqual(elrs.kind,'compound')
        self.assertLess(max(model.ELRS_COLOUR),0.08)
        self.assertLess(max(model.ELRS_HUB_COLOUR),0.08)

    def test_elrs_manual_feed_fields_no_longer_visible(self):
        self.assertIn('VTXAntennaHeadColour',FIELD_LOCATION)
        self.assertNotIn('ELRSTReferenceStemLength',FIELD_LOCATION)
        self.assertNotIn('ELRSTReferenceFeedPreset',FIELD_LOCATION)

    def test_v0911_custom_dimensions_migrate_without_overriding(self):
        old=Parameters().to_dict()
        old.update(VTXAntennaReferenceLength=64.,VTXAntennaReferenceDiameter=7.,
                   ELRSTReferenceSpan=83.,ELRSTReferenceStemLength=18.)
        for key in ('VTXAntennaReferencePreset','ELRSTReferencePreset','ELRSTReferenceFeedPreset'):
            old.pop(key,None)
        restored=Parameters.from_dict(old)
        self.assertEqual(restored.VTXAntennaReferencePreset,'Custom')
        self.assertEqual(restored.ELRSTReferencePreset,'Custom')
        self.assertEqual(restored.ELRSTReferenceFeedPreset,'Custom')
        self.assertAlmostEqual(vtx_spec(restored)['length'],64.)
        self.assertAlmostEqual(elrs_spec(restored)['span'],83.)
        self.assertAlmostEqual(elrs_spec(restored)['feed_length'],18.)

    def test_reference_dimensions_roundtrip_through_json(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            p=replace(Parameters(),VTXAntennaReferenceLength=64.,ELRSTReferenceSpan=93.)
            path=Path(directory)/'frame.json'
            save_parameters(path,p)
            self.assertEqual(load_parameters(path),p)


if __name__=='__main__':unittest.main()
