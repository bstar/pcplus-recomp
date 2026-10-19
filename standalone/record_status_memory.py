#!/usr/bin/env python3
"""Bind redisplay's moved storage to the actual terminal and regressions."""
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest_path = ROOT / 'build/terminal/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    binary = ROOT / 'build/terminal/TERMINAL.EXE'
    digest = sha(binary)
    assert digest == manifest['binary_sha256']
    memory = manifest['memory_layout']
    assert memory['near_bytes'] == 64096 and memory['near_spare_bytes'] == 1440
    assert memory['redisplay_row_index_bytes'] == 494 and memory['redisplay_row_index_offset'] == 63000
    image = binary.read_bytes()
    header_bytes = struct.unpack_from('<H', image, 8)[0] * 16
    config = next(s for s in memory['code_segments'] if s['name'] == 'CONFIG_CODE')
    base = config['relative_segment'] * 16 + config['offset']
    code = image[header_bytes + base:header_bytes + base + config['bytes']]
    source = (ROOT / 'src/redisplay/redisplay.c').read_text()
    texts = re.findall(r'static const char REDISPLAY_TEXT (\w+)\[\]="([^"\n]*)";', source)
    assert len(texts) == 14
    positions = {}
    for name, text in texts:
        raw = text.encode('cp437') + b'\0'
        offset = code.find(raw)
        assert offset >= 0, name
        positions[name] = dict(config_offset=offset, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    assert sum(v['bytes'] for v in positions.values()) == 902
    reports = {}
    paths = ('build/terminal/redisplay-checks.json', 'build/redisplay-dos/checks.json',
             'build/history-export-dos/checks.json', 'build/clipboard-live-dos/checks.json',
             'build/aspect-when-renderer-dos/memory-44a477/checks.json',
             'build/bbs-lab/script-login/memory-44a477-sync/checks.json',
             'build/bbs-lab/script-login/memory-44a477-enigma30/checks.json',
             'docs/validation/application-components-source-build.json')
    for name in paths:
        path = ROOT / name
        report = json.loads(path.read_text())
        assert report['passed'], name
        if name.startswith('docs/validation/'):
            binding = report['outputs']['terminal/TERMINAL.EXE']
            assert binding['matches_workspace'] and binding['sha256'] == binding['workspace_sha256'] == digest
        elif name.startswith('build/aspect-when') or name.startswith('build/bbs-lab'):
            assert report['terminal_sha256'] == digest
            assert report['runner_sha256'] == sha(ROOT / 'build/aspect-runner/ASPECT.EXE')
        else:
            assert report['binary_sha256'] == digest
        reports[name] = dict(sha256=sha(path), result=report)
    files = ('src/redisplay/redisplay.c', 'src/terminal/redisplay.asm',
             'standalone/terminal_memory.py', 'standalone/record_status_memory.py',
             'docs/STATUS_MEMORY.md')
    result = dict(schema='status-memory-v1', passed=True, terminal_sha256=digest,
                  baseline=dict(terminal_sha256='dacbd777fbd5afaf441ad46ec559be2b95c53fd5ba9c1219ebfb865cd48e66ae',
                                near_bytes=65488, near_spare_bytes=48),
                  memory=memory, fixed_text=positions, reports=reports,
                  sources={name: sha(ROOT / name) for name in files},
                  scope='Memory prerequisite for SET/status integration. Existing behavior and source builds checked; native status/RPC remains unfinished. ENiGMA passes only the explicit30ms-buffered regression, not immediate forwarding or physical modem testing.')
    out = ROOT / 'docs/validation/status-memory.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
