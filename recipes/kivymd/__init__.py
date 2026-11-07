"""Build the pinned KivyMD sdist; its 1.2.0 release has no PyPI wheel."""
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


recipe = KivyMDRecipe()
