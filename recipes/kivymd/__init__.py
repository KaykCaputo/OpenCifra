"""Build the pinned KivyMD sdist; its 1.2.0 release has no PyPI wheel."""
from pathlib import Path
import shutil
from pythonforandroid.recipe import PythonRecipe


class KivyMDRecipe(PythonRecipe):
    version = '1.2.0'
    url = ('https://files.pythonhosted.org/packages/20/81/'
           '0b1154f5e581d5910702d9fadb3217f56cb186f72c8b36de0271e7ff9b5c/'
           'kivymd-{version}.tar.gz')
    sha256sum = '2d33e2c59259998e93aee55acde647a4a20e5a0f962469db24ee4c9ec586962e'
    depends = ['python3', 'kivy', 'pillow']
    call_hostpython_via_targetpython = False
    setup_extra_args = ['--no-deps']

    def postbuild_arch(self, arch):
        # Upstream setup.py splits absolute paths at the first "kivymd/".
        # p4a nests that name repeatedly, so its wheel omits all dynamic KV data.
        # Also runs with cached Python installs, repairing previously built ABIs.
        source = Path(self.get_build_dir(arch.arch)) / 'kivymd'
        target = Path(self.ctx.get_python_install_dir(arch.arch)) / 'kivymd'
        for path in source.rglob('*'):
            if path.is_file() and path.suffix in {'.kv', '.ttf', '.png', '.po', '.pot'}:
                destination = target / path.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
        if not (target / 'uix/button/button.kv').is_file():
            raise RuntimeError('KivyMD UI resources are missing after installation')


recipe = KivyMDRecipe()
