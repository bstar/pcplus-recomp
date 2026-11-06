#!/usr/bin/env python3
"""Audit measured compiler choices and retained memory against a disabled control.

This is an artifact/layout check; DOS and BBS behavior require separate reports.
"""
import argparse
import json
from pathlib import Path
from build_path_session import ROOT, object_segments, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('control', 'terminal', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    control, terminal, out = a.control.resolve(), a.terminal.resolve(), a.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    manifests = []
    for binary in (control, terminal):
        assert binary.is_relative_to(ROOT / 'build')
        m = json.loads(binary.with_name('manifest.json').read_text())
        assert sha(binary) == m['binary_sha256'] and not m.get('original_inputs')
        for name, digest in m['sources'].items():
            assert sha(ROOT / name) == digest, name
        manifests.append(m)
    left, right = manifests
    assert not left['experimental_optimize_size'] and right['experimental_optimize_size']
    assert {k: v for k, v in left.items() if k.startswith('experimental_') and k != 'experimental_optimize_size'} == {
        k: v for k, v in right.items() if k.startswith('experimental_') and k != 'experimental_optimize_size'}
    assert left['packed_command_ui'] == right['packed_command_ui']
    path = ROOT / 'standalone/terminal_size_profile.json'
    profile = json.loads(path.read_text())
    assert profile['version'] == 1
    assert set(right['optimized_c_sources']) == set(profile['sources'])
    rows = []
    for name, entry in profile['sources'].items():
        assert sha(ROOT / name) == entry['source_sha256'], name
        assert right['optimized_c_sources'][name] == profile['compiler_options'][entry['profile']]
        measured = []
        for binary in (control, terminal):
            obj = binary.parent / (Path(name).stem + '.obj')
            segments = object_segments(obj)
            code = sum(s['bytes'] for s in segments.values() if s['class'] in ('CODE', 'FARCODE'))
            data = sum(s['bytes'] for s in segments.values() if s['class'] not in ('CODE', 'FARCODE'))
            measured.append([code, data])
        assert measured == [entry['control_code_data_bytes'], entry['optimized_code_data_bytes']], name
        assert measured[0][1] == measured[1][1] and measured[1][0] < measured[0][0], name
        rows.append(dict(source=name, profile=entry['profile'], control=measured[0], optimized=measured[1], saved=measured[0][0]-measured[1][0]))
    assert sum(r['saved'] for r in rows) == profile['potential_object_saving_bytes']
    old, new = left['memory_layout'], right['memory_layout']
    capacities = ['near_bytes', 'far_bytes', 'history_bytes', 'native_reset_private_stack_bytes',
                  'native_reset_shadow_bytes', 'native_reset_workspace_bytes', 'snapshot_bytes',
                  'far_ui_storage_bytes', 'redisplay_snapshot_bytes', 'redisplay_row_index_bytes']
    for key in capacities:
        assert old[key] == new[key], key
    saved = old['minimum_allocated_module_bytes'] - new['minimum_allocated_module_bytes']
    assert saved > 0 and saved == 16 * (old['retained_parent_paragraphs'] - new['retained_parent_paragraphs'])
    out.mkdir(parents=True)
    result = dict(passed=True, control_sha256=sha(control), binary_sha256=sha(terminal),
                  retained_bytes_saved=saved, object_bytes_saved=sum(r['saved'] for r in rows),
                  capacities={k: new[k] for k in capacities}, rows=rows,
                  sources={n: sha(ROOT/n) for n in ['standalone/check_terminal_size_profile.py',
                           'standalone/build_path_session.py', 'standalone/terminal_size_profile.json']},
                  scope=__doc__)
    (out / 'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS', len(rows), 'measured sources;', saved, 'retained bytes saved; capacities unchanged')


if __name__ == '__main__':
    main()
