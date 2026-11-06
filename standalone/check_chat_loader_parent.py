#!/usr/bin/env python3
"""Bind the resident parent loader objects to the actual DOS overlay tests.

No foreground Chat behavior or shared-storage ownership is established here.
"""
import argparse
import json
from pathlib import Path
from build_path_session import ROOT, sha, object_segments
from omf_imports import records


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('terminal', 'fixture', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    binary, fixture, out = a.terminal.resolve(), a.fixture.resolve(), a.output.resolve()
    assert all(p.is_relative_to(ROOT/'build') for p in (binary, fixture, out))
    assert not out.exists()
    m = json.loads(binary.with_name('manifest.json').read_text())
    r = json.loads((fixture/'result.json').read_text())
    assert r['passed']
    assert m['experimental_chat_loader'] and r['loader_compiler_flags'] == ['-ox', '-os', '-oe=0']
    assert r['loads'] == 6 and r['relocation_areas'] == 2 and r['free_paragraphs_during_load'] == 0
    assert r['composed_frames'] == 568 and r['composed_effects'] == 1071
    assert sha(binary) == m['binary_sha256']
    for report in (m, r):
        for n, h in report['sources'].items():
            assert sha(ROOT/n) == h, n
    for n, h in r['artifacts'].items():
        assert sha(fixture/n) == h, n
    assert (binary.parent/'chat-module/expected.h').read_bytes() == (fixture/'module/expected.h').read_bytes()
    matches = {}
    for parent, tested in [('chat-loader.obj', 'loader.obj'), ('chat-load-kernel.obj', 'load.obj')]:
        before = records((binary.parent/parent).read_bytes())
        after = records((fixture/'drive'/tested).read_bytes())
        assert len(before) == len(after), parent
        differences = 0
        for left, right in zip(before, after):
            if left == right:
                continue
            # Only the generated header's dependency comment may differ:
            # Watcom records its build-directory path and DOS timestamp here.
            # All code, data, symbols, fixups and other metadata stay exact.
            assert parent == 'chat-loader.obj' and left[0] == right[0] == 0x88
            for record, expected in [(left, binary.parent/'chat-module/expected.h'),
                                     (right, fixture/'module/expected.h')]:
                payload = record[1]
                assert payload[:2] == b'\x80\xe9' and payload[6] == len(payload)-7
                assert payload[7:] == str(expected).encode()
            differences += 1
        assert differences <= 1
        matches[parent] = dict(parent_sha256=sha(binary.parent/parent),
                               fixture_sha256=sha(fixture/'drive'/tested),
                               generated_header_dependency_differences=differences)
        segments = object_segments(binary.parent/parent)
        assert all(not s['bytes'] for n, s in segments.items() if n != 'CHAT_LOAD_CODE')
    module = binary.parent/'PCCHAT.OVL'
    assert module.read_bytes() == (fixture/'module/PCCHAT.OVL').read_bytes()
    assert sha(module) == r['module_sha256'] == m['chat_loader']['module']['binary_sha256']
    bank = next(s for s in m['memory_layout']['code_segments'] if s['name']=='CHAT_LOAD_CODE')
    assert bank['bytes'] == m['chat_loader']['code_bytes'] == 1264
    assert m['chat_loader']['near_data_bytes'] == 0
    assert not m['chat_loader']['foreground_binding'] and not m['chat_loader']['storage_lease']
    listing = binary.with_name('terminal.map').read_text()
    assert '_chat_module_dispatch' not in listing and 'CHAT_CODE ' not in listing
    out.mkdir(parents=True)
    record = dict(passed=True, binary_sha256=sha(binary), module_sha256=sha(module),
                  tested_loader_objects=matches, loader_code_bytes=bank['bytes'],
                  near_data_bytes=0, minimum_module_bytes=m['memory_layout']['minimum_allocated_module_bytes'],
                  reports={str((fixture/'result.json').relative_to(ROOT)):sha(fixture/'result.json')},
                  sources={'standalone/check_chat_loader_parent.py':sha(Path(__file__))},
                  scope=__doc__+' OMF code/data/symbols/fixups and separate MZ module match DOS-tested bytes. Only one generated expected.h dependency path/timestamp comment may differ, with its contents checked identical. Parent has no static Chat implementation. Application admission and physical acceptance require separate evidence.')
    (out/'result.json').write_text(json.dumps(record, indent=2)+'\n')
    print('PASS real parent retains DOS-tested loader code/data/fixups; separate exact Chat module')


if __name__ == '__main__':
    main()
