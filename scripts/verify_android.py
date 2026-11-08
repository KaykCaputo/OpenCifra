"""Check the final APK/AAB for runtime resources before distributing it."""
import argparse
from io import BytesIO
from pathlib import Path
import tarfile
from zipfile import ZipFile

KV_RESOURCES = (
    'card/card', 'dialog/dialog', 'selection/selection', 'swiper/swiper',
    'imagelist/imagelist', 'textfield/textfield', 'toolbar/toolbar',
    'filemanager/filemanager', 'datatables/datatables', 'snackbar/snackbar',
    'expansionpanel/expansionpanel', 'dropdownitem/dropdownitem', 'label/label',
    'tooltip/tooltip', 'slider/slider', 'navigationrail/navigationrail',
    'selectioncontrol/selectioncontrol', 'menu/menu', 'tab/tab', 'banner/banner',
    'segmentedbutton/segmentedbutton', 'sliverappbar/sliverappbar',
    'segmentedcontrol/segmentedcontrol', 'bottomsheet/bottomsheet', 'backdrop/backdrop',
    'chip/chip', 'refreshlayout/refreshlayout', 'navigationdrawer/navigationdrawer',
    'button/button', 'spinner/spinner', 'progressbar/progressbar', 'list/list',
    'pickers/datepicker/datepicker', 'pickers/colorpicker/colorpicker',
    'pickers/timepicker/timepicker', 'bottomnavigation/bottomnavigation',
)


def verify(path):
    failures = []
    with ZipFile(path) as archive:
        prefix = 'base/' if path.suffix == '.aab' else ''
        with tarfile.open(fileobj=BytesIO(archive.read(prefix + 'assets/private.tar'))) as private:
            app_files = {name.removeprefix('./') for name in private.getnames()}
        for name in ('ui.kv', 'guitar.json', 'RobotoMono-Regular.ttf', 'icon.png'):
            if name not in app_files:
                failures.append('App: ' + name)
        bundles = [n for n in archive.namelist() if n.startswith(prefix + 'lib/') and n.endswith('/libpybundle.so')]
        if not bundles:
            failures.append('No Python bundles')
        for bundle in bundles:
            arch = bundle.split('/')[-2]
            with tarfile.open(fileobj=BytesIO(archive.read(bundle))) as package:
                names = {name.removeprefix('./') for name in package.getnames()}
            root = '_python_bundle/site-packages/'
            required = ['kivymd/uix/' + item + '.kv' for item in KV_RESOURCES]
            required += ['kivymd/fonts/Roboto-Regular.ttf', 'kivymd/fonts/materialdesignicons-webfont.ttf']
            required += [module + '/__init__.pyc' for module in ('kivy', 'kivymd', 'requests', 'bs4', 'charset_normalizer', 'soupsieve')]
            for resource in required:
                if root + resource not in names:
                    failures.append(arch + ': ' + resource)
    if failures:
        raise ValueError('Missing Android runtime resources:\n' + '\n'.join(failures))
    return len(bundles)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact', type=Path)
    args = parser.parse_args()
    try:
        count = verify(args.artifact)
    except (ValueError, KeyError, tarfile.TarError) as error:
        parser.exit(1, str(error) + '\n')
    print(f'Verified {args.artifact.name}: {count} ABIs, all {len(KV_RESOURCES)} KivyMD layouts and startup assets.')
