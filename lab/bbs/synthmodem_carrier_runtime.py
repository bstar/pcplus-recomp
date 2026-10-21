#!/usr/bin/env python3
"""Stage the carrier client/helper/backend on the accepted lifecycle runtime."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import subprocess
from synthmodem_vm_control import ROOT, sha, records, archive
from synthmodem_lifecycle_runtime import validate as validate_lifecycle

LEDGER = ROOT / 'docs/validation/synthmodem-carrier-runtime.json'
REFERENCE = ROOT / 'build/bbs-lab/synthmodem-lifecycle-runtime-01/runtime'
HERE = ROOT / 'lab/bbs/patches/synthmodem-carrier'


def validate(runtime):
    ledger = json.loads(LEDGER.read_text())
    assert ledger['passed']
    expected = ledger['files']
    assert {str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file()} == set(expected)
    for name, digest in expected.items(): assert sha(runtime/name) == digest, name
    return {str(runtime/name): digest for name, digest in expected.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve(); assert out.is_relative_to(ROOT/'build')
    inputs = validate_lifecycle(REFERENCE)
    client = json.loads((ROOT/'docs/validation/synthmodem-carrier-client.json').read_text())
    helper = json.loads((ROOT/'docs/validation/synthmodem-carrier-helper.json').read_text())
    assert client['passed'] and helper['passed']
    frozen_names = ['lab/bbs/synthmodem_carrier_runtime.py', 'lab/bbs/synthmodem_lifecycle_runtime.py',
                    'lab/bbs/synthmodem_vm_control.py', 'nix/flake.nix', 'nix/flake.lock',
                    'nix/slmodem.nix', 'nix/slmodem-sources.json', 'nix/slmodem-carrier.nix',
                    'nix/control-carrier.nix', 'tools/build-slmodem-carrier', 'tools/build-control-carrier',
                    'docs/validation/synthmodem-carrier-client.json', 'docs/validation/synthmodem-carrier-helper.json']
    frozen_names += [str(p.relative_to(ROOT)) for p in HERE.iterdir() if p.is_file()]
    frozen = {name: sha(ROOT/name) for name in frozen_names}
    builds = {}
    for name, tool, filename, expected in [
        ('modem', 'tools/build-slmodem-carrier', 'slmodemd', client['modem_executable_sha256']),
        ('helper', 'tools/build-control-carrier', 'modemd-ctrl', helper['helper_sha256'])]:
        result = json.loads(subprocess.check_output([str(ROOT/tool), '--no-link', '--json'], text=True))
        executable = Path(result[0]['outputs']['out'])/'bin'/filename
        assert sha(executable) == expected
        builds[name] = {'build': result, 'executable': str(executable), 'sha256': expected}
    out.mkdir(parents=True, exist_ok=False)
    runtime = out/'runtime'; shutil.copytree(REFERENCE, runtime)
    subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(HERE/'backend.patch')],
                   cwd=runtime/'source', check=True)
    original = records(gzip.decompress((REFERENCE/'candidate.cpio.gz').read_bytes()))
    entries = []; changed_entries = []
    for name, fields, body in original:
        replacement = body
        if name == 'usr/local/bin/slmodemd': replacement = Path(builds['modem']['executable']).read_bytes()
        if name == 'usr/local/bin/modemd-ctrl': replacement = Path(builds['helper']['executable']).read_bytes()
        if name == 'etc/init.d/S99modem-pjsip':
            replacements = [
                (b'PTY_LINK=/tmp/ttySL0', b'PTY_LINK=/tmp/ttySL0\nCARRIER_PATH=/tmp/synthmodem-carrier.sock'),
                (b"       SYNTHMODEM_BUILD_ID='pjsip-vm'", b"       SYNTHMODEM_CARRIER_PATH='$CARRIER_PATH' \\\n       SYNTHMODEM_BUILD_ID='pjsip-vm'"),
                (b'"exec \\"$SLMODEMD\\" -d2', b'"SYNTHMODEM_CARRIER_PATH=\'$CARRIER_PATH\' exec \\"$SLMODEMD\\" -d2')]
            for before, after in replacements:
                assert replacement.count(before) == 1, before
                replacement = replacement.replace(before, after)
        if replacement != body: changed_entries.append(name)
        entries.append((name, fields, replacement))
    assert sorted(changed_entries) == ['etc/init.d/S99modem-pjsip', 'usr/local/bin/modemd-ctrl', 'usr/local/bin/slmodemd']
    entries.append(('TRAILER!!!', [0]*13, b''))
    image = runtime/'candidate.cpio.gz'; image.write_bytes(gzip.compress(archive(entries), mtime=0))
    rebuilt = records(gzip.decompress(image.read_bytes())); assert len(rebuilt) == len(original)
    for (name, fields, body), (newname, newfields, newbody) in zip(original, rebuilt):
        assert name == newname and fields[:6]+fields[7:] == newfields[:6]+newfields[7:]
        assert name in changed_entries or body == newbody
    changed_files = [str(Path(name).relative_to(REFERENCE)) for name, digest in inputs.items()
                     if sha(runtime/Path(name).relative_to(REFERENCE)) != digest]
    assert sorted(changed_files) == ['candidate.cpio.gz', 'source/src/backends/PjsipBackend.js']
    assert all(sha(Path(name)) == digest for name, digest in inputs.items())
    assert all(sha(ROOT/name) == digest for name, digest in frozen.items())
    result = {'passed': True, 'reference': str(REFERENCE.relative_to(ROOT)),
              'runtime_inputs': inputs, 'frozen_inputs': frozen, 'builds': builds,
              'changed_files': changed_files, 'changed_archive_entries': changed_entries,
              'files': {str(p.relative_to(runtime)):sha(p) for p in runtime.rglob('*') if p.is_file()},
              'scope': 'Exact carrier-mode staging on the lifecycle runtime. Only backend source, two modem/helper executables and their shared init environment change. No installed service or runtime acceptance.'}
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'passed': True, 'runtime': str(runtime), 'changed_files': changed_files}, indent=2))


if __name__ == '__main__': main()
