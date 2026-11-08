"""Portable coverage of the STL-driven bumper STEP writer (without FreeCAD)."""
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from freecad.rotorforge.step_safety import (
    faceted_solid_from_mesh, export_bumper_mesh_steps,
)


class BBox:
    def __init__(self, xmin=0, ymin=0, zmin=0, lx=20, ly=8, lz=3):
        self.XMin, self.YMin, self.ZMin = xmin, ymin, zmin
        self.XLength, self.YLength, self.ZLength = lx, ly, lz


class Solid:
    def __init__(self, bbox=None, volume=100., fail=False):
        self.BoundBox = bbox or BBox()
        self.Volume = volume
        self.Solids = [self]
        self.fail = fail
    def isNull(self): return False
    def isValid(self): return True
    def reverse(self): self.Volume = -self.Volume
    def copy(self):
        b = self.BoundBox
        return Solid(BBox(b.XMin, b.YMin, b.ZMin, b.XLength, b.YLength, b.ZLength), self.Volume, self.fail)
    def translate(self, delta):
        b = self.BoundBox
        b.XMin += delta[0]
        b.YMin += delta[1]
        b.ZMin += delta[2]
    def exportStep(self, path):
        if self.fail:
            Path(path).write_bytes(b'incomplete')
            raise IOError('write failed')
        Path(path).write_bytes(b'STEP' * 100)


class FakePartShape:
    def __init__(self):
        self.Shells = ['shell']
        self.Faces = []
    def makeShapeFromMesh(self, topology, tolerance):
        assert topology == 'mesh topology'
        assert tolerance < 0.01


class Mesh:
    def __init__(self, closed=True):
        self.Topology = 'mesh topology'
        self.closed = closed
    def isSolid(self): return self.closed


class Tests(unittest.TestCase):
    def deps(self, solid=None):
        return patch.dict(sys.modules, {
            'Part': types.SimpleNamespace(Shape=FakePartShape,
                                          makeSolid=lambda shell: solid or Solid()),
            'FreeCAD': types.SimpleNamespace(Vector=lambda x,y,z: (x,y,z))
        })

    def test_mesh_produces_two_steps_with_frame_offset(self):
        with self.deps(), tempfile.TemporaryDirectory() as tmp:
            assembled = Solid(BBox(44, -54, 6))
            printable = Solid()
            print_path, assembly_path = export_bumper_mesh_steps(assembled, printable, Mesh(), tmp)
            self.assertTrue(print_path.is_file())
            self.assertTrue(assembly_path.is_file())
            self.assertGreater(print_path.stat().st_size, 256)
            self.assertEqual(list(Path(tmp).glob('*.pending.step')), [])

    def test_open_mesh_is_rejected_without_bad_step(self):
        with self.deps(), tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'watertight'):
                export_bumper_mesh_steps(Solid(), Solid(), Mesh(closed=False), tmp)
            self.assertEqual(list(Path(tmp).glob('*.step')), [])

    def test_invalid_step_writer_does_not_leave_partial_files(self):
        with self.deps(Solid(fail=True)), tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(IOError):
                export_bumper_mesh_steps(Solid(), Solid(), Mesh(), tmp)
            self.assertFalse(list(Path(tmp).glob('*.step')))

    def test_dimensions_must_match(self):
        with self.deps(Solid(BBox(lx=21))), tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'dimensions differ'):
                export_bumper_mesh_steps(Solid(), Solid(), Mesh(), tmp)
            self.assertFalse(list(Path(tmp).glob('*.step')))

    def test_volume_must_match(self):
        with self.deps(Solid(volume=60)), tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'volume disagrees'):
                export_bumper_mesh_steps(Solid(), Solid(), Mesh(), tmp)
            self.assertFalse(list(Path(tmp).glob('*.step')))

    def test_no_bumper_steps_from_original_cad_path(self):
        source = (Path(__file__).resolve().parents[1] / 'freecad' / 'rotorforge' / 'exporters.py').read_text(encoding='utf-8')
        self.assertIn('export_bumper_mesh_steps(', source)
        self.assertIn("mesh.write(str(soft_folder/(role+'.stl')))", source)
        self.assertLess(source.index("mesh.write(str(soft_folder/(role+'.stl')))"), source.index('export_bumper_mesh_steps('))
        self.assertIn("'FrontBumper_STEP_WARNING.txt'", source)


if __name__ == '__main__': unittest.main()
