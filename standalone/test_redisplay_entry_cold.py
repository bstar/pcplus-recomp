#!/usr/bin/env python3
"""Build and replay the Redisplay component from a minimal public source export."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from build_redisplay_entry import ROOT, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    origin, output = args.build.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((origin / 'manifest.json').read_text())
    sources = dict(manifest['sources'])
    for name in ('standalone/check_redisplay_entry.py', 'standalone/test_redisplay_entry_cold.py'):
        sources[name] = sha(ROOT / name)
    export = output / 'public-source'
    for name, digest in sources.items():
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts
        assert path.parts[0] in ('reconstruction', 'standalone')
        assert sha(ROOT / path) == digest
        target = export / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)
    assert sorted(str(p.relative_to(export)) for p in export.rglob('*') if p.is_file()) == sorted(sources)
    assert not any((p / '.git').exists() for p in [export, *export.parents])
    built = output / 'rebuilt'
    with (output / 'build.log').open('w') as log:
        subprocess.run([sys.executable, str(export / 'standalone/build_redisplay_entry.py'),
                        '--output', str(built)], cwd=export, stdout=log, stderr=log, check=True, timeout=30)
    with (output / 'cpu.log').open('w') as log:
        subprocess.run([sys.executable, str(export / 'standalone/check_redisplay_entry.py'),
                        '--output', str(built)], cwd=export, stdout=log, stderr=log, check=True, timeout=180)
    fresh = json.loads((built / 'manifest.json').read_text())
    cpu = json.loads((built / 'cpu.json').read_text())
    assert fresh['passed'] and cpu['passed'] and fresh['original_inputs'] == cpu['original_inputs'] == []
    assert fresh['units'] == manifest['units'] and fresh['sources'] == manifest['sources']
    assert cpu['cases'] == 3460 and cpu['original_comparisons'] == 0
    assert cpu['checker_sha256'] == sources['standalone/check_redisplay_entry.py']
    for name, digest in manifest['artifacts'].items():
        if name.endswith('.bin'):
            assert fresh['artifacts'][name] == sha(built / name) == digest
    report = dict(passed=True, source_only=True, original_inputs=[], source_files=len(sources),
                  sources=sources, original_manifest_sha256=sha(origin / 'manifest.json'),
                  rebuilt_manifest_sha256=sha(built / 'manifest.json'), cpu_sha256=sha(built / 'cpu.json'),
                  CPU_cases=cpu['cases'], checker_sha256=sha(Path(__file__)),
                  scope='Minimal exported public sources; no originals, analysis images, prior objects or Git ancestry. Same exact flat instructions and CPU checks; no live application integration.')
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'sources'}, indent=2))


if __name__ == '__main__':
    main()
