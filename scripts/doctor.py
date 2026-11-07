"""Report capabilities without changing the system or opening the microphone."""
import importlib.metadata
import shutil
import sys

print('Python:', sys.version.split()[0])
for name in ('Kivy', 'KivyMD', 'requests', 'beautifulsoup4', 'numpy', 'sounddevice', 'ruff', 'pyinstaller', 'buildozer'):
    try:
        print(f'{name}: {importlib.metadata.version(name)}')
    except importlib.metadata.PackageNotFoundError:
        print(f'{name}: not installed')
for command in ('java', 'adb', 'gh', 'Xvfb', 'git'):
    print(f'{command}: {shutil.which(command) or "not installed"}')
print('Android builds need the Buildozer OS prerequisites; see README.md.')
