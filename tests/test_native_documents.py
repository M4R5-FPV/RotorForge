"""Check bundled native document identity, links and restorable proxy paths."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = sorted(ROOT.rglob('*.FCStd'))
PROXY_CLASSES = {'ParameterProxy', 'PartProxy', 'ParameterViewProvider'}


class NativeDocumentTests(unittest.TestCase):
    def test_document_links_resolve_after_metadata_updates(self):
        self.assertTrue(DOCUMENTS)
        for path in DOCUMENTS:
            with self.subTest(document=path.name), ZipFile(path) as archive:
                self.assertIsNone(archive.testzip())
                root = ET.fromstring(archive.read('Document.xml'))
                names = [obj.get('name') for obj in root.findall('Objects/Object')]
                self.assertEqual(len(names), len(set(names)))
                known = set(names)
                self.assertEqual(known, {obj.get('name') for obj in root.findall('ObjectData/Object')})
                for node in root.findall('Objects/ObjectDeps'):
                    self.assertIn(node.get('Name'), known)
                    for dependency in node.findall('Dep'):
                        self.assertIn(dependency.get('Name'), known)
                for link in root.iter('Link'):
                    if link.get('value'):
                        self.assertIn(link.get('value'), known)
                if 'GuiDocument.xml' in archive.namelist():
                    gui = ET.fromstring(archive.read('GuiDocument.xml'))
                    for provider in gui.iter('ViewProvider'):
                        self.assertIn(provider.get('name'), known)

    def test_frame_groups_and_property_metadata_use_rotorforge(self):
        for path in DOCUMENTS:
            with self.subTest(document=path.name), ZipFile(path) as archive:
                root = ET.fromstring(archive.read('Document.xml'))
                groups = []
                for obj in root.findall('ObjectData/Object'):
                    for prop in obj.findall('Properties/Property'):
                        if prop.get('name') == 'Generator':
                            groups.append(obj)
                            self.assertTrue(obj.get('name').startswith('RotorForge'))
                            label = obj.find("Properties/Property[@name='Label']/String")
                            self.assertTrue(label.get('value').startswith('RotorForge'))
                        if prop.get('name') in {'Generator', 'Parameters', 'FrameRole'}:
                            self.assertEqual(prop.get('group'), 'RotorForge')
                        if prop.get('name') == 'GeneratorVersion':
                            self.assertEqual(prop.get('doc'), 'RotorForge plugin version')
                self.assertTrue(groups)

    def test_all_frame_proxies_use_the_installed_module(self):
        for path in DOCUMENTS:
            with self.subTest(document=path.name), ZipFile(path) as archive:
                found = set()
                if path.parent.name=='examples':
                    self.assertIn('GuiDocument.xml',archive.namelist())
                for name in ('Document.xml', 'GuiDocument.xml'):
                    if name not in archive.namelist():
                        continue
                    for proxy in ET.fromstring(archive.read(name)).iter('Python'):
                        if proxy.get('class') in PROXY_CLASSES:
                            found.add(proxy.get('class'))
                            # Older fixtures retain the compatibility bridge; new native files use the canonical namespace.
                            self.assertIn(proxy.get('module'), {'rotorforge.document','freecad.rotorforge.document'})
                self.assertTrue({'ParameterProxy', 'PartProxy'} <= found)
                if path.parent.name=='examples':
                    self.assertIn('ParameterViewProvider',found)


if __name__ == '__main__':
    unittest.main()
