"""Run Buildozer with stable pip tooling and redact secrets from build output."""
from pathlib import Path
import os
import re
import signal
import subprocess
import sys
import time

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


def main():
    environment = os.environ.copy()
    environment['VIRTUAL_ENV'] = sys.prefix
    environment['PATH'] = str(Path(sys.executable).parent) + os.pathsep + environment.get('PATH', '')
    environment['PIP_CONSTRAINT'] = str(ROOT / 'scripts/android-constraints.txt')
    if any(command in sys.argv[1:] for command in ('debug', 'release')):
        repair_pip_environments()
    buildozer = Path(sys.executable).with_name('buildozer')
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
    return process.wait()


if __name__ == '__main__':
    raise SystemExit(main())
