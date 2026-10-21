#!/usr/bin/env python3
"""Combine the pinned normal post-training runtime with existing PCM export.

Only the boot archive differs from the normal runtime. The diagnostic image
adds the previously validated export daemon/init hook; all modem binaries and
JavaScript match the normal runtime exactly. No installed service is changed.
"""
import argparse
import gzip
import json
import shutil
from pathlib import Path
from synthmodem_vm_control import ROOT, records, sha
from synthmodem_posttrain_validation import validate as validate_normal
from synthmodem_key_framing_runtime import validate as validate_framed

NORMAL = ROOT / 'build/bbs-lab/synthmodem-posttrain-runtime-01/runtime'
TRACE = ROOT / 'build/bbs-lab/synthmodem-key-framing-trace-runtime-01/runtime'
LEAF = 'source/src/session/CallSession.js'


def validate(runtime, proof):
    runtime = Path(runtime).resolve()
    proof = Path(proof).resolve()
    assert runtime.is_relative_to(ROOT / 'build') and proof.is_relative_to(ROOT / 'build')
    result = json.loads(proof.read_text())
    assert result['passed'] and result['changed_files_vs_normal'] == ['candidate.cpio.gz']
    assert result['stager_sha256'] == sha(Path(__file__))
    assert result['normal_inputs'] == validate_normal(NORMAL)
    assert result['trace_reference_inputs'] == validate_framed(TRACE, trace=True)
    assert {str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file()} == set(result['files'])
    assert all(sha(runtime / name) == h for name, h in result['files'].items())
    return {str(runtime / name): h for name, h in result['files'].items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    normal = validate_normal(NORMAL)
    trace = validate_framed(TRACE, trace=True)
    out.mkdir(parents=True)
    runtime = out / 'runtime'
    shutil.copytree(TRACE, runtime)
    shutil.copyfile(NORMAL / LEAF, runtime / LEAF)
    normal_names = {str(Path(n).relative_to(NORMAL)) for n in normal}
    assert {str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file()} == normal_names
    changed = [name for name in sorted(normal_names) if sha(runtime / name) != sha(NORMAL / name)]
    assert changed == ['candidate.cpio.gz']
    normal_entries = {n: (f, b) for n, f, b in records(gzip.decompress((NORMAL / 'candidate.cpio.gz').read_bytes()))}
    trace_entries = {n: (f, b) for n, f, b in records(gzip.decompress((runtime / 'candidate.cpio.gz').read_bytes()))}
    assert set(trace_entries) == set(normal_entries) | {'lab-trace-export.sh'}
    changed_entries = []
    for name, (fields, body) in normal_entries.items():
        other_fields, other_body = trace_entries[name]
        assert fields[:6] + fields[7:] == other_fields[:6] + other_fields[7:], name
        if body != other_body:
            changed_entries.append(name)
            marker = b'    echo "S99modem-pjsip: starting backend B"'
            assert name == 'etc/init.d/S99modem-pjsip' and body.count(marker) == 1
            assert other_body == body.replace(marker, b'    /bin/sh /lab-trace-export.sh &\n' + marker)
    assert changed_entries == ['etc/init.d/S99modem-pjsip']
    assert trace_entries['lab-trace-export.sh'][1] == (ROOT / 'lab/bbs/receive_trace_export.sh').read_bytes()
    assert all(sha(Path(n)) == h for n, h in {**normal, **trace}.items())
    result = dict(passed=True, audio_runtime_accepted=False, normal_inputs=normal,
                  trace_reference_inputs=trace, changed_files_vs_normal=changed,
                  changed_archive_entries=changed_entries, added_archive_entries=['lab-trace-export.sh'],
                  stager_sha256=sha(Path(__file__)),
                  files={str(p.relative_to(runtime)): sha(p) for p in runtime.rglob('*') if p.is_file()},
                  scope='Diagnostic-only PCM-export init hook/daemon from the pinned trace image. All normal post-training JavaScript, DSP/helper/d-modem binaries, kernel and other archive metadata/content are exact. The existing QEMU wrapper adds the separate export chardev. Stage identity only; no runtime/audio/BBS/physical acceptance.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    assert validate(runtime, out / 'result.json')
    print(json.dumps(dict(passed=True, runtime=str(runtime), changed_files=changed)))


if __name__ == '__main__':
    main()
