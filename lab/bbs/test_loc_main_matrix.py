#!/usr/bin/env python3
"""Eight admitted layouts of authenticated LoC art, menu return and focused input."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from product_inputs import ROOT, select_product, sha
from enigma_loc_menu_fixture import verify


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out, candidate = a.output.resolve(), a.candidate.resolve()
    assert out.is_relative_to(ROOT/'build')
    out.mkdir(parents=True,exist_ok=False)
    binary, files = select_product(a.terminal,'TERMINAL.EXE')
    meta = verify(candidate)
    names = ['lab/bbs/test_loc_main_matrix.py','lab/bbs/test_loc_main_dos.py',
             'lab/bbs/audit_loc_main_dos.py','lab/bbs/enigma_loc_menu_fixture.py',
             'lab/bbs/synthmodem_proxy_serial.js','lab/bbs/test_dos.py',
             'lab/bbs/audit_screen_reference.py','lab/bbs/audit_size_probe_screen.py',
             'standalone/test_ansi_reference_dos.py','standalone/reference_watch.asm']
    files += [ROOT/name for name in names]+[candidate/name for name in meta['fixture_inputs']]
    frozen = {str(path.relative_to(ROOT)):sha(path) for path in files}
    cases = []
    for rows in (25,28,43,50):
        for hidden in (0,1):
            label = out.name+'-'+str(rows)+'-'+str(hidden)
            with (out/(label+'.log')).open('w') as log:
                r = subprocess.run([sys.executable,str(ROOT/'lab/bbs/test_loc_main_dos.py'),
                    '--candidate',str(candidate),'--runtime',str(a.runtime.resolve()),
                    '--terminal',str(binary),'--label',label,'--rows',str(rows),'--hidden',str(hidden)],
                    cwd=ROOT,stdout=log,stderr=log,timeout=195)
            assert r.returncode==0,('producer',label)
            capture = ROOT/'build/bbs-lab/results/enigma'/label
            bridge = ROOT/'build/bbs-lab'/(label+'-proxy')
            with (out/(label+'-audit.log')).open('w') as log:
                r = subprocess.run([sys.executable,str(ROOT/'lab/bbs/audit_loc_main_dos.py'),
                    '--output',str(capture),'--bridge',str(bridge)],cwd=ROOT,stdout=log,stderr=log,timeout=30)
            assert r.returncode==0,('audit',label)
            path = capture/'loc-main-audit.json'
            audit = json.loads(path.read_text())
            assert audit['passed'] and audit['matched_reference_cells']==(rows-(not hidden))*80
            cases.append(dict(physical_rows=rows,status_hidden=hidden,logical_rows=rows-(not hidden),
                reference_cells=audit['matched_reference_cells'],source_model_cells=audit['matched_source_art_cells'],
                actual_CPR=audit['actual_CPR'],capture=str(capture.relative_to(ROOT)),bridge=str(bridge.relative_to(ROOT)),
                audit_path=str(path.relative_to(ROOT)),audit_sha256=sha(path),passed=True))
            print(label,'PASS',audit['matched_reference_cells'],'cells',flush=True)
    assert sum(c['reference_cells'] for c in cases)==23040
    for name,digest in frozen.items():
        assert sha(ROOT/name)==digest,name
    verify(candidate)
    result = dict(passed=True,cases=cases,terminal_sha256=sha(binary),sources=frozen,
        matched_reference_cells=23040,matched_source_model_cells=sum(c['source_model_cells'] for c in cases),
        scope=__doc__+' Paced DOS8086 synthetic Hayes/staged proxy and copied module/form on isolated stock core. No live-board, whole application or physical acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    main()
