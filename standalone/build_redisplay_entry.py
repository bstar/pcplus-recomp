#!/usr/bin/env python3
"""Source-only exact flat and relocatable native Redisplay entry services."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'reconstruction/redisplay_entry'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    proof = json.loads((CORE / 'provenance.json').read_text())
    sources = [Path(__file__), CORE / 'provenance.json', ROOT / 'reconstruction/uart/encodings.inc']
    dependencies = []
    for name, flag, selected in [
            ('program_display', 'PROGRAM_DISPLAY_OMF', {'snapshot', 'restore', 'snow_disable', 'snow_enable'}),
            ('notice_window', 'NOTICE_WINDOW_OMF', {'cursor_push', 'cursor_pop', 'cursor_get'}),
            ('program_ui', 'PROGRAM_DISPLAY_OMF', {'cursor'})]:
        provenance = ROOT / 'reconstruction' / name / 'provenance.json'
        sources.append(provenance)
        prior = json.loads(provenance.read_text())
        assert prior['original_sha256'] == proof['original_sha256']
        found = [dict(u, omf_define=flag) for u in prior['units'] if Path(u['file']).stem in selected]
        assert len(found) == len(selected)
        dependencies.extend(found)
    units = [dict(u, omf_define='REDISPLAY_ENTRY_OMF') for u in proof['units']] + dependencies
    for unit in units:
        path = ROOT / unit['file']
        sources.append(path)
        for fmt, suffix, flags in [('bin', '.bin', []), ('obj', '.obj', ['-D' + unit['omf_define']])]:
            target = output / (path.stem + suffix)
            subprocess.run(['nasm', '-f' + fmt, *flags,
                            '-I' + str(ROOT / 'reconstruction/uart') + '/',
                            str(path), '-o', str(target)], check=True)
            if fmt == 'bin':
                assert target.stat().st_size == unit['bytes'] and sha(target) == unit['sha256'], path
    caller = ROOT / 'standalone/redisplay_chat_sequence.asm'
    sources.append(caller)
    subprocess.run(['nasm', '-fbin', str(caller), '-o', str(output / 'chat_sequence.bin')], check=True)
    result = dict(passed=True, original_inputs=[], units=units,
                  source_bytes=sum(u['bytes'] for u in proof['units']),
                  dependency_bytes=sum(u['bytes'] for u in dependencies),
                  sources={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  artifacts={p.name: sha(p) for p in sorted(output.iterdir())},
                  limitations=proof['limitations'],
                  scope='Native component only; flat byte identity and OMF emission. No application selection or deployment.')
    (output / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
