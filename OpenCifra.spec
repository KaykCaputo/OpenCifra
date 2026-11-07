# Native desktop package. Build independently on each supported desktop OS.
from PyInstaller.utils.hooks import collect_all

md_data, md_binaries, md_hidden = collect_all('kivymd')
a = Analysis(['main.py'], pathex=[], binaries=md_binaries,
    datas=md_data + [(name, '.') for name in
        ('ui.kv', 'guitar.json', 'RobotoMono-Regular.ttf', 'icon.png', 'LICENSE')] +
        [('opentuna/LICENSE.md', 'opentuna')],
    hiddenimports=md_hidden + ['sounddevice', 'opentuna.audio_engine'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='OpenCifra',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, icon='icon.png')
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='OpenCifra')
