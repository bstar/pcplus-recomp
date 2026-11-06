#!/usr/bin/env python3
"""Record actual parent/child/open failures separately from BBS acceptance."""
import argparse
import json
import struct
from pathlib import Path
from build_path_session import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    session = args.session.resolve()
    output = args.output.resolve()
    assert session.is_relative_to(ROOT / 'build')
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    captured = session / 'ADMIT.BIN'
    raw = captured.read_bytes()
    assert len(raw) in (36,102)
    words = struct.unpack_from('<18H', raw)
    assert words[:2] == (0xad41, 1) and all(words[i] for i in [2, 3, 4])
    assert words[5] == 5 and words[6:9] == (0, 0, 1)
    assert words[10:14] == (0, 0, 1, words[9])
    producer_path = session / 'proxy-integration.json'
    producer = json.loads(producer_path.read_text())
    base = json.loads((session / 'result.json').read_text())
    assert not producer['passed'] and not producer['checks']['actual_ASPECT_login']
    assert base['checks']['hardware_restored'] and base['checks']['dos_normal_exit']
    assert (session / 'BEFORE.BIN').read_bytes() == (session / 'AFTER.BIN').read_bytes()
    for name, expected in producer['product_inputs'].items():
        assert sha(ROOT / name) == expected, name
    observer_segment = struct.unpack('<H', (session / 'VFSEG.BIN').read_bytes())[0]
    helper_segment = struct.unpack('<H', (session / 'KEYSEG.BIN').read_bytes())[0]
    assert observer_segment >= 0xa000 and helper_segment >= 0xa000
    wrapper = ROOT / 'build/admission-watch-extended-wrapper-20261106/result.json'
    checked = json.loads(wrapper.read_text())
    assert checked['passed'] and len(checked['cases']) == 16
    for name, expected in checked['sources'].items():
        assert sha(ROOT / name) == expected, name

    def bind(path):
        return dict(path=str(path.relative_to(ROOT)), sha256=sha(path))

    result = dict(passed=True, binary_sha256=producer['binary_sha256'],
                  interpreter_sha256=producer['interpreter_sha256'], session=bind(producer_path),
                  capture=bind(captured), wrapper_checks=bind(wrapper), observer_words=words,
                  observer_segment=observer_segment, keyboard_helper_segment=helper_segment,
                  DOS_EXEC_succeeded=True, DOS_EXEC_error=0, child_termination_type=0,
                  child_exit_code=1, ASPECT_exit_meaning='Exit1 alone does not establish entry to ASPECT main or ASPECT_RUN_OPEN.',
                  matching_script_open_calls=words[14],
                  last_open=dict(function=words[17], carry=bool(words[15] & 1), ax=words[16]) if words[14] else None,
                  hardware_restored=True, application_accepted=False, deployment_changed=False,
                  sources={n: sha(ROOT / n) for n in ['standalone/record_program_admission.py',
                           'lab/bbs/program_admission_support.py', 'standalone/program_admission_watch.inc']},
                  limits=['Read-only parent timer witness and DOS3D/6C wrapper for owned SYNC.ASX only.',
                          'No caller memory modifications or fabricated DOS results; wrapper checks cover flags/register/stack preservation.',
                          'Cannot-open exit is established; heap exhaustion versus another CRT/path cause requires further evidence.',
                          'This diagnostic is a failed Synchronet workflow, never BBS acceptance.',
                          'Earlier observer attempts left extra diagnostic vectors installed; excluded from hardware-restoration claims.',
                          'No production package, private settings or service changes.'])
    output.mkdir()
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['DOS_EXEC_succeeded', 'child_exit_code',
                     'matching_script_open_calls', 'last_open', 'hardware_restored', 'application_accepted']}))


if __name__ == '__main__':
    main()
