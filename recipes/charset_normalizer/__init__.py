"""Use the portable Python implementation, not a host/Android binary wheel."""
from pythonforandroid.recipe import PythonRecipe


class CharsetNormalizerRecipe(PythonRecipe):
    version = '3.5.2'
    url = ('https://files.pythonhosted.org/packages/33/1c/'
           'f41d4e74c28ab327ff3acd36053f7ea506c55872d7a90b0fa71aa3ab0c89/'
           'charset_normalizer-{version}.tar.gz')
    sha256sum = '39de2a259fc954455c57274dc94c79d5842774e1247a016aff30bc0efed0f4ef'
    depends = ['python3']
    call_hostpython_via_targetpython = False
    setup_extra_args = ['--no-deps']

    def get_recipe_env(self, arch=None, with_flags_in_cc=True):
        env = super().get_recipe_env(arch, with_flags_in_cc)
        env['CHARSET_NORMALIZER_USE_CYTHON'] = '0'
        return env


recipe = CharsetNormalizerRecipe()
