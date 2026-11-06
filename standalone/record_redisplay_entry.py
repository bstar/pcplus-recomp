#!/usr/bin/env python3
"""Bind source, paired instruction replay, cold rebuild and static REA evidence."""
import argparse
import json
import struct
from pathlib import Path
from build_redisplay_entry import ROOT, CORE, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--cold', type=Path, required=True)
    p.add_argument('--rea-snapshot', type=Path, required=True)
    args = p.parse_args()
    built, cold = args.build.resolve(), args.cold.resolve()
    manifest = json.loads((built / 'manifest.json').read_text())
    source, original = [json.loads((built / n).read_text()) for n in ('cpu.json', 'cpu-original.json')]
    clean = json.loads((cold / 'result.json').read_text())
    proof = json.loads((CORE / 'provenance.json').read_text())
    assert manifest['passed'] and manifest['original_inputs'] == []
    for report in (source, original):
        assert report['passed'] and report['cases'] == 3460
        assert report['manifest_sha256'] == sha(built / 'manifest.json')
        assert report['checker_sha256'] == sha(ROOT / 'standalone/check_redisplay_entry.py')
    assert source['original_inputs'] == [] and source['original_comparisons'] == 0
    assert original['original_comparisons'] == 3460
    assert original['original_inputs'] == [dict(path='analysis/pcplus-originals/PCPLUS-main-2.01.EXE',
                                               sha256=proof['original_sha256'])]
    for path, digest in manifest['sources'].items():
        assert sha(ROOT / path) == digest, path
    for name, digest in manifest['artifacts'].items():
        assert sha(built / name) == digest, name
    assert clean['passed'] and clean['source_only'] and clean['original_inputs'] == []
    assert clean['original_manifest_sha256'] == sha(built / 'manifest.json')
    assert clean['CPU_cases'] == 3460 and clean['checker_sha256'] == sha(Path(__file__).with_name('test_redisplay_entry_cold.py'))
    for path, digest in clean['sources'].items():
        assert sha(ROOT / path) == sha(cold / 'public-source' / path) == digest
    assert clean['rebuilt_manifest_sha256'] == sha(cold / 'rebuilt/manifest.json')
    assert clean['cpu_sha256'] == sha(cold / 'rebuilt/cpu.json')

    # Original lookup is an explicitly separate analyst audit; ordinary source
    # compilation and both source-only checks above do not read these files.
    original_path = ROOT / original['original_inputs'][0]['path']
    assert sha(original_path) == proof['original_sha256']
    image = original_path.read_bytes()
    ranges_path = ROOT / 'analysis/pcplus-overlay-entry-images/manifest.json'
    assert sha(ranges_path) == proof['source_mapping_manifest_sha256']
    ranges = json.loads(ranges_path.read_text())
    assert ranges['original_sha256'] == proof['original_sha256']
    carrier = next(i for i in ranges['images'] if i['overlay'] == 15)
    carrier_path = ranges_path.parent / carrier['file']
    assert sha(carrier_path) == carrier['sha256'] == proof['static_carrier_sha256']
    raw = carrier_path.read_bytes()
    header = struct.unpack_from('<H', raw, 8)[0] * 16
    loader = json.loads((ROOT / 'analysis/pcplus-overlays/manifest.json').read_text())
    assert loader['source_sha256'] == proof['original_sha256']
    records = json.loads(args.rea_snapshot.read_text())['evidence_bundle']['records']
    records = {r['evidence_id']: r for r in records}
    recovered = []
    for unit in proof['units']:
        start, end, at = unit['start'], unit['end'], unit['file_offset']
        assert unit['bytes'] == end - start
        region = unit['mapping']
        assert region in carrier['source_ranges']
        assert region['relative_address'] <= start < end <= region['relative_address'] + region['bytes']
        assert at == region['source_file_offset'] + start - region['relative_address']
        assert image[at:at + unit['bytes']] == raw[header + start:header + end] == (built / (Path(unit['file']).stem + '.bin')).read_bytes()
        assert all(not (at < t['file_offset'] + 12 and t['file_offset'] < at + unit['bytes']) for t in loader['trampolines'])
        record = records[unit['rea_evidence_id']]
        assert record['operation'] == 'inspect_analysis_view'
        assert record['subject']['digest']['sha256'] == carrier['sha256']
        view = record['normalized_result']
        assert view['coverage']['exhausted'] and view['coverage']['next_offset'] is None
        assert view['procedure_address'] == hex(0x10000 + start)
        assert view['item'][0].startswith(hex(0x10000 + start) + ':')
        assert view['item'][-1].startswith(hex(0x10000 + end - (3 if Path(unit['file']).stem == 'restore_or_alert' else 1)) + ': RET')
        recovered.append(dict(unit=Path(unit['file']).stem, evidence_id=record['evidence_id'],
                              original_file_offset=at, instructions=len(view['item']),
                              original_slice_and_unpatched_loader_mapping_matched=True))
    result = dict(passed=True, component_only=True, whole_application_gates_closed=[],
                  application_selected_or_deployed=False, build_original_inputs=[],
                  recovered_bytes=manifest['source_bytes'], dependency_bytes=manifest['dependency_bytes'],
                  source_only_CPU_cases=source['cases'], analyst_paired_original_cases=original['original_comparisons'],
                  cold_source_only_CPU_cases=clean['CPU_cases'],
                  original_sha256=proof['original_sha256'], sources=clean['sources'],
                  artifacts=manifest['artifacts'], units=manifest['units'], REA=recovered,
                  checks=['Direct entry and a diagnostic caller with the recovered Chat save/enter/restore/show call sequence.',
                          'Nested cursor stack with zero and seven existing frames, direct CRT and BIOS cursor paths.',
                          '80-column frames of25/28/43/50 rows, both conditional cursor-policy branches, arithmetic wrap.',
                          'Empty, nonempty and wrapped history, including head=start/end-1 and noncanonical nonzero wrapped flag.',
                          'Actual recovered copy/restore/free instructions, saved-screen guards, exact cursor/stack/DS=SS return.',
                          'Failed allocation still invokes viewer/empty notice and NULL cleanup alerts without copy/free.',
                          'All four zero/nonzero offset/segment pointer classes in shared restore wrapper.',
                          'Configured mouse-scale restoration intentionally differs from pre-entry runtime value.',
                          'Minimal public-source rebuild without originals, analysis inputs, prior objects or Git ancestry.'],
                  evidence=dict(build_manifest=sha(built / 'manifest.json'), source_CPU=sha(built / 'cpu.json'),
                                paired_original_CPU=sha(built / 'cpu-original.json'), cold=sha(cold / 'result.json'),
                                private_REA_snapshot=sha(args.rea_snapshot)),
                  recorder_sha256=sha(Path(__file__)), limitations=proof['limitations'] +
                  ['CPU replay uses declared viewer/heap/BIOS/CRT/alert endpoints; it is not original whole-program execution, DOS or physical/acoustic testing.',
                   'The loadable Chat module and maintained viewer still share frozen storage. Nested storage, RX service, unfinished input, file operations and cancellation/carrier-loss integration remain open.'])
    destination = ROOT / 'docs/validation/redisplay-entry.json'
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print('Recorded190 new exact native bytes;3460 source cases,3460 paired original comparisons,3460 cold source cases. Live integration remains open.')


if __name__ == '__main__':
    main()
