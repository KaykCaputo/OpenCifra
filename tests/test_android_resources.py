from io import BytesIO
from pathlib import Path
import tarfile
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts.release import package
from zipfile import ZipFile

from scripts.android import repair_ui_distributions
from scripts.verify_android import KV_RESOURCES, verify


def tar_bytes(names):
    output = BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as archive:
        for name in names:
            entry = tarfile.TarInfo(name)
            entry.size = 1
            archive.addfile(entry, BytesIO(b'x'))
    return output.getvalue()


class AndroidResourceTests(unittest.TestCase):
    def make_apk(self, path, omit=None):
        with ZipFile(path, 'w') as archive:
            archive.writestr('assets/private.tar', tar_bytes(['ui.kv', 'guitar.json', 'RobotoMono-Regular.ttf', 'icon.png']))
            for arch in ('arm64-v8a', 'armeabi-v7a'):
                names = ['kivymd/uix/' + item + '.kv' for item in KV_RESOURCES]
                names += ['kivymd/fonts/Roboto-Regular.ttf', 'kivymd/fonts/materialdesignicons-webfont.ttf']
                names += [m + '/__init__.pyc' for m in ('kivy', 'kivymd', 'requests', 'bs4', 'charset_normalizer', 'soupsieve')]
                if arch == 'arm64-v8a' and omit:
                    names.remove(omit)
                archive.writestr('lib/' + arch + '/libpybundle.so', tar_bytes(
                    ['_python_bundle/site-packages/' + name for name in names]))

    def test_missing_layout_in_one_abi_rejects_apk(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'app.apk'
            self.make_apk(path, omit='kivymd/uix/button/button.kv')
            with self.assertRaisesRegex(ValueError, 'arm64-v8a: kivymd/uix/button/button.kv'):
                verify(path)
            self.make_apk(path)
            self.assertEqual(verify(path), 2)

    def test_missing_cached_layout_rebuilds_distribution_not_native_recipes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            platform = root / '.buildozer/android/platform/build-example'
            dist = platform / 'dists/open_cifra'
            resources = dist / '_python_bundle__arm64-v8a/_python_bundle/site-packages/kivymd'
            resources.mkdir(parents=True)
            compiled = platform / 'build/other_builds/native.so'
            compiled.parent.mkdir(parents=True)
            compiled.write_bytes(b'compiled')
            repair_ui_distributions(root)
            self.assertFalse(dist.exists())
            self.assertEqual(len(list((platform / 'compat-backups').iterdir())), 1)
            self.assertEqual(compiled.read_bytes(), b'compiled')
            resources.mkdir(parents=True)
            for name in KV_RESOURCES:
                path = resources / ('uix/' + name + '.kv')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            repair_ui_distributions(root)
            self.assertTrue(dist.exists())

    def test_release_package_excludes_old_apk_and_checks_current_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'bin').mkdir()
            (root / 'bin/open_cifra-0.3-arm64-v8a-release.apk').write_bytes(b'old broken APK')
            current = root / 'bin/open_cifra-0.3.1-arm64-v8a-release.apk'
            self.make_apk(current)
            target = root / 'assets'
            with patch('scripts.release.ROOT', root):
                package(SimpleNamespace(version='0.3.1', assets=str(target)))
            self.assertEqual({p.name for p in target.iterdir()}, {current.name, 'SHA256SUMS'})
            self.assertIn(current.name, (target / 'SHA256SUMS').read_text())

    def test_release_package_rejects_current_apk_missing_layouts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'bin').mkdir()
            current = root / 'bin/open_cifra-0.3.1-arm64-v8a-release.apk'
            self.make_apk(current, omit='kivymd/uix/card/card.kv')
            with patch('scripts.release.ROOT', root), self.assertRaises(ValueError):
                package(SimpleNamespace(version='0.3.1', assets=str(root / 'assets')))
