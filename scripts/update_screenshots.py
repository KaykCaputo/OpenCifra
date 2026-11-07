"""Capture the running UI with original demo content, then refresh README images."""
from pathlib import Path
import subprocess
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
subprocess.run(['xvfb-run', '-a', sys.executable, 'tests/ui_smoke.py'], cwd=ROOT, check=True)
for source, destination in [('home', 'screenshot1.jpeg'), ('song', 'screenshot2.jpeg'),
                            ('lists', 'screenshot3.jpeg'), ('tuner', 'screenshot4.jpeg')]:
    image = Image.open('/tmp/opencifra-' + source + '.png').convert('RGB')
    image.save(ROOT / destination, 'JPEG', quality=94, subsampling=0)
    print(f'Updated {destination}: {image.width} x {image.height}')
