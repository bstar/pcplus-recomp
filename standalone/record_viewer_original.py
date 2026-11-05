#!/usr/bin/env python3
"""Check complete original viewer frames against explicit generated-file expectations."""
import argparse, hashlib, json, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
FOOTER = b' Home: Top of file      PgUp: Previous page      PgDn: Next page      ESC: Exit '
CASES = ['long', 'binary', 'empty', 'unterminated', 'no-lf', 'exact-page', 'large', 'retry']

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def expected(rows):
    assert len(rows) <= 24 and all(len(r) <= 80 for r in rows)
    rows = rows + [b''] * (24 - len(rows)) + [FOOTER]
    return b''.join(bytes((c, 0x71 if i == 24 else 7))
                    for i, row in enumerate(rows) for c in row.ljust(80, b' '))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); base = a.input.resolve(); out = a.output.resolve()
    assert base.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    def bind(path):
        return dict(path=str(path.relative_to(ROOT)), sha256=sha(path))
    wanted = {
        'long': [b'L'*79+b'A', b'M'*80, b'X'*80, b'', b'Y'*80, b'2', b'DONE'],
        'binary': [b'TAB\tMID', b'C\rR', b'NUL', b'Z\x1aAFTER', b'E\x1b[31mRED',
                   bytes([0x80, 0x81, 0xdb, 0xb0, 0xff]), b'TRAIL'],
        'empty': [], 'unterminated': [b'NO FINAL NEWLINE'],
        'no-lf': [b'A'*80]*3+[b'A'],
        'exact-page': [('L%03d'%i).encode() for i in range(1, 25)],
        'large': [('L%04d'%i).encode()+b'X'*75 for i in range(529, 553)],
        'retry': [b'FOUND AFTER RETRY']}
    sources = ['standalone/test_viewer_original_dos.py', 'standalone/viewer_original_watch.asm',
               'standalone/record_viewer_original.py']
    rows = []
    for case in CASES:
        d = base/case; r = json.loads((d/'result.json').read_text())
        assert r['case'] == case and r['original_sha256'] == ORIGINAL and r['done']
        assert r['producer_sha256'] == sha(ROOT/sources[0])
        assert r['payload_unchanged'] and r['original_unchanged'] and r['exit_CWD'] == 'C:\\'
        assert sha(d/'c/PCPLUS.EXE') == ORIGINAL and sha(d/'c/PAGE.DAT') == r['payload_sha256']
        raw = (d/'c/EDITVIEW.BIN').read_bytes(); magic, count, ticks = struct.unpack_from('<3H', raw)
        assert magic == 0x4544 and ticks > 70 and count == len(r['frames'])
        assert count == (1 if case == 'large' else 7 if case in ['retry','exact-page'] else 5)
        frames = []
        for i, meta in enumerate(r['frames']):
            f = (d/f'frame-{i}.bin').read_bytes(); cursor, shape = struct.unpack_from('<2H',raw,6+i*4004)
            assert len(f) == 4000 and f == raw[10+i*4004:4010+i*4004]
            assert sha(d/f'frame-{i}.bin') == meta['sha256']
            assert [cursor>>8,cursor&255] == meta['cursor'] and shape == meta['shape']
            frames.append(f)
        index = 0 if case == 'large' else 4 if case == 'retry' else 2
        assert frames[index] == expected(wanted[case]), case
        assert r['frames'][index]['cursor'] == [100,200] and r['frames'][index]['shape'] == 0x0607
        checks = dict(normal_exit=True, original_and_payload_unchanged=True,
                      exact_2000_cells=True, exact_hidden_cursor_and_shape=True)
        if case != 'large':
            restored = 5 if case in ['retry','exact-page'] else 3
            assert frames[0] == frames[restored]
            assert r['frames'][0]['cursor'] == r['frames'][restored]['cursor']
            assert r['frames'][0]['shape'] == r['frames'][restored]['shape']
            checks['exact_terminal_restore'] = True
        if case == 'exact-page':
            assert frames[3] == expected([]) and frames[4] == frames[2]
            checks['blank_page_after_exact_boundary_and_pageup_restore'] = True
        if case == 'retry':
            assert b'FILE NOT FOUND...' in frames[2][1920:2080:2]
            assert frames[1] == frames[3]
            checks['missing_file_acknowledge_retry'] = True
        if case == 'large':
            assert r['payload_bytes'] == 95040 and 528*132 == 69696
            checks['page23_after_64k_offset'] = True
        rows.append(dict(case=case, checks=checks, matched_cells=2000, keys=r['keys'],
                         report=bind(d/'result.json'), observer=bind(d/'watch.asm'),
                         captures=[bind(d/f'frame-{i}.bin') for i in range(count)]))
    bundle = ROOT/'analysis/viewer-page-recovery-20261105.json'
    records = json.loads(bundle.read_text())['records']
    evidence = [r['evidence_id'] for r in records]
    result = dict(passed=True, original_sha256=ORIGINAL, cases=rows,
        sources={n:sha(ROOT/n) for n in sources}, static_bundle=bind(bundle), evidence_ids=evidence,
        prior_unaccepted_retry=bind(ROOT/'build/viewer-original-20261105/retry/result.json'),
        scope='Eight unmodified-original DOSBox8086 offline workflows, generated files, dummy UART. Exact full viewer frames including raw control/CP437 bytes, clipping, empty/unterminated/EOF paging, retry and32-bit seek. Passive seven-frame timer sample is not a complete event trace. No analysis-image execution, maintained-viewer implementation, DOS6.22 or physical acceptance claim.',
        remaining=['Maintained serviced viewer and file-handle lifecycle/fault tests.',
                   'Configured external-viewer PRM binding and launch integration.',
                   'Native100-page limit is static inference, not runtime verified.'])
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS eight original viewer workflows,16000 complete viewer cells,exact restore/retry/EOF and69696-byte seek')

if __name__ == '__main__':
    main()
