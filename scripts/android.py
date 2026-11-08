"""Run Buildozer with stable pip tooling and redact secrets from build output."""
from pathlib import Path
import os
import re
import signal
import subprocess
import sys
import time

try:
    from .verify_android import KV_RESOURCES, verify
except ImportError:
    from verify_android import KV_RESOURCES, verify

ROOT = Path(__file__).resolve().parents[1]
PINNED_PIP = '25.3'
SENSITIVE = re.compile(r'PASSWORD|PASSWD|TOKEN|SECRET|PRIVATE_KEY|API_KEY', re.I)


def redact(line, environment):
    # Covers Buildozer's environment dump and known values inside other messages.
    if re.search(r'(?:PASSWORD|PASSWD|TOKEN|SECRET|PRIVATE_KEY|API_KEY)\s*=', line, re.I):
        return line.split('=', 1)[0] + '= [REDACTED]\n'
    for key, value in environment.items():
        if SENSITIVE.search(key) and value:
            line = line.replace(value, '[REDACTED]')
    return line


def repair_pip_environments(root=ROOT):
    for venv in root.glob('.buildozer/android/platform/build-*/build/venv'):
        installed = list(venv.glob('lib/python*/site-packages/pip-*.dist-info'))
        if installed and {p.name for p in installed} != {f'pip-{PINNED_PIP}.dist-info'}:
            backup = venv.with_name(f'venv-before-repair-{time.time_ns()}')
            venv.rename(backup)
            print(f'Rebuilding mixed-version pip environment; backup: {backup}', flush=True)


def repair_ui_distributions(root=ROOT):
    for dist in root.glob('.buildozer/android/platform/build-*/dists/*'):
        bundles = list(dist.glob('_python_bundle__*/_python_bundle/site-packages/kivymd'))
        if bundles and any(not (bundle / ('uix/' + name + '.kv')).is_file()
                           for bundle in bundles for name in KV_RESOURCES):
            backup = dist.parent.parent / 'compat-backups' / f'{dist.name}-{time.time_ns()}'
            backup.parent.mkdir(parents=True, exist_ok=True)
            dist.rename(backup)
            print(f'Rebuilding distribution missing KivyMD layouts; backup: {backup}', flush=True)


def main():
    environment = os.environ.copy()
    environment['VIRTUAL_ENV'] = sys.prefix
    environment['PATH'] = str(Path(sys.executable).parent) + os.pathsep + environment.get('PATH', '')
    environment['PIP_CONSTRAINT'] = str(ROOT / 'scripts/android-constraints.txt')
    if any(command in sys.argv[1:] for command in ('debug', 'release')):
        repair_pip_environments()
        repair_ui_distributions()
    buildozer = Path(sys.executable).with_name('buildozer')
    previous = {p: p.stat().st_mtime_ns for p in (ROOT / 'bin').glob('*') if p.is_file()}
    process = subprocess.Popen([str(buildozer), *sys.argv[1:]], cwd=ROOT,
        env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, errors='replace', bufsize=1, start_new_session=True)
    def stop(signum, frame):
        try:
            os.killpg(process.pid, signum)
        except ProcessLookupError:
            pass
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        for line in process.stdout:
            sys.stdout.write(redact(line, environment))
            sys.stdout.flush()
    finally:
        process.stdout.close()
    result = process.wait()
    if result == 0 and any(command in sys.argv[1:] for command in ('debug', 'release')):
        for path in (ROOT / 'bin').glob('*'):
            if path.suffix in ('.apk', '.aab') and path.stat().st_mtime_ns != previous.get(path):
                verify(path)
                print(f'Runtime assets verified: {path.name}', flush=True)
    return result


if __name__ == '__main__':
    raise SystemExit(main())
