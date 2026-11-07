from pathlib import Path
import tempfile
import unittest

from scripts.android import redact, repair_pip_environments


class AndroidBuildTests(unittest.TestCase):
    def test_redacts_environment_dump_and_embedded_values(self):
        env = {'P4A_RELEASE_KEYSTORE_PASSWD': 'sample-secret', 'PATH': '/usr/bin'}
        self.assertNotIn('sample-secret', redact("# P4A_RELEASE_KEYSTORE_PASSWD = 'sample-secret'\n", env))
        self.assertNotIn('sample-secret', redact('Signing failed with sample-secret\n', env))
        self.assertEqual(redact('Building Kivy\n', env), 'Building Kivy\n')
        self.assertNotIn('another-secret', redact("# OTHER_API_KEY = 'another-secret'\n", env))

    def test_mixed_pip_is_backed_up_without_touching_compiled_recipes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build = root / '.buildozer/android/platform/build-example/build'
            venv = build / 'venv'
            packages = venv / 'lib/python3.14/site-packages'
            for version in ('25.3', '26.3'):
                (packages / f'pip-{version}.dist-info').mkdir(parents=True)
            compiled = build / 'other_builds/kivy/compiled.so'
            compiled.parent.mkdir(parents=True)
            compiled.write_bytes(b'compiled library')
            repair_pip_environments(root)
            self.assertFalse(venv.exists())
            self.assertEqual(len(list(build.glob('venv-before-repair-*'))), 1)
            self.assertEqual(compiled.read_bytes(), b'compiled library')
            (packages / 'pip-25.3.dist-info').mkdir(parents=True)
            repair_pip_environments(root)
            self.assertTrue(venv.exists())
            self.assertEqual(len(list(build.glob('venv-before-repair-*'))), 1)
