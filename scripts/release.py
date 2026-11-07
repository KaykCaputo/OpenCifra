"""Build artifact handling and explicit, validated GitHub release operations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def fail(message):
    raise SystemExit(message)


def files(directory):
    return sorted(p for p in directory.iterdir() if p.is_file() and p.name != 'SHA256SUMS') if directory.exists() else []


def checksum(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def package(args):
    target = Path(args.assets).resolve()
    target.mkdir(parents=True, exist_ok=True)
    desktop = ROOT / 'dist/OpenCifra'
    if desktop.exists():
        name = f'OpenCifra-{args.version}-{platform.system().lower()}-{platform.machine()}'
        shutil.make_archive(str(target / name), 'zip', desktop.parent, desktop.name)
    for artifact in (ROOT / 'bin').glob('*'):
        if artifact.suffix in ('.apk', '.aab'):
            shutil.copy2(artifact, target / artifact.name)
    artifacts = files(target)
    if not artifacts:
        fail('No artifacts. Run make build-desktop or make android-debug first.')
    (target / 'SHA256SUMS').write_text(''.join(f'{checksum(p)}  {p.name}\n' for p in artifacts))
    print(f'Packaged {len(artifacts)} artifacts in {target}')


def validate(args):
    version = re.search(r'^version\s*=\s*(\S+)', (ROOT / 'buildozer.spec').read_text(), re.M)[1]
    if args.tag != 'v' + version:
        fail(f'Tag must match buildozer.spec: v{version}')
    if run('git', 'status', '--porcelain'):
        fail('Commit or stash local changes before releasing.')
    if run('git', 'rev-list', '-n', '1', args.tag) != run('git', 'rev-parse', 'HEAD'):
        fail('The release tag must point at HEAD.')
    run('gh', 'auth', 'status')
    # Verify the tag exists on the selected GitHub repository and resolves to HEAD.
    remote_sha = run('gh', 'api', f'repos/{args.repo}/commits/{args.tag}', '--jq', '.sha')
    if remote_sha != run('git', 'rev-parse', 'HEAD'):
        fail('Push the exact release tag to the selected GitHub repository first.')
    target = Path(args.assets)
    artifacts = files(target)
    if not artifacts or not (target / 'SHA256SUMS').is_file():
        fail('Missing artifacts/checksums. Run make package first.')
    expected = ''.join(f'{checksum(p)}  {p.name}\n' for p in artifacts)
    if (target / 'SHA256SUMS').read_text() != expected:
        fail('Artifact checksums changed. Run make package again.')
    return artifacts + [target / 'SHA256SUMS']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['package', 'check', 'draft', 'publish', 'signing-check', 'clean'])
    parser.add_argument('--version', default='0.3')
    parser.add_argument('--tag', default='v0.3')
    parser.add_argument('--repo', default='KaykCaputo/OpenCifra')
    parser.add_argument('--assets', default='dist/release')
    args = parser.parse_args()
    if args.action == 'package':
        package(args)
    elif args.action == 'signing-check':
        names = ['P4A_RELEASE_KEYSTORE', 'P4A_RELEASE_KEYSTORE_PASSWD',
                 'P4A_RELEASE_KEYALIAS', 'P4A_RELEASE_KEYALIAS_PASSWD']
        missing = [name for name in names if not os.environ.get(name)]
        if missing:
            fail('Set signing environment variables: ' + ', '.join(missing))
        if not Path(os.environ['P4A_RELEASE_KEYSTORE']).is_file():
            fail('Signing keystore does not exist.')
        print('Signing configuration present.')
    elif args.action == 'clean':
        for name in ('build', 'dist'):
            directory = ROOT / name
            if directory.is_symlink():
                fail('Refusing to clean a symlink: ' + str(directory))
            if directory.exists():
                shutil.rmtree(directory)
    else:
        artifacts = validate(args)
        if args.action == 'draft':
            run('gh', 'release', 'create', args.tag, '--repo', args.repo, '--verify-tag', '--draft',
                '--title', f'OpenCifra {args.tag}', '--generate-notes', *map(str, artifacts))
            print('Draft uploaded. Review it before make release-publish.')
        elif args.action == 'publish':
            release = json.loads(run('gh', 'api', f'repos/{args.repo}/releases/tags/{args.tag}'))
            if not release['draft']:
                fail('Release is already published.')
            uploaded = {asset['name']: asset for asset in release['assets']}
            if set(uploaded) != {p.name for p in artifacts}:
                fail('Draft assets do not match local artifacts.')
            for path in artifacts:
                if uploaded[path.name].get('digest') != 'sha256:' + checksum(path):
                    fail('Draft asset digest missing or different: ' + path.name)
            run('gh', 'release', 'edit', args.tag, '--repo', args.repo, '--draft=false', '--verify-tag')
            print('Release published.')
        else:
            print('Release checks passed.')


if __name__ == '__main__':
    main()
