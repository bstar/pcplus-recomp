#!/usr/bin/env python3
"""Check receipt rejection using corrupted copies, preserving live evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import record_hook_bbs as audit

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True)
    p.add_argument('--terminal',type=Path,required=True);p.add_argument('--runner',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    stage=ROOT/'build/bbs-lab/script-login'/args.label
    output=ROOT/'build/bbs-lab/results/enigma'/args.label
    report=json.loads((stage/'checks.json').read_text())
    terminal=args.terminal.resolve();runner=args.runner.resolve()
    with tempfile.TemporaryDirectory(prefix='hook-bbs-audit-',dir=ROOT/'build') as temporary:
        clone=Path(temporary);audit.ROOT=clone
        for folder in (stage,output):shutil.copytree(folder,clone/folder.relative_to(ROOT))
        for relative in report['sources']:
            target=clone/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,target)
        for relative in report['server_sources']:
            source=ROOT/'build/bbs-lab/enigma/source'/relative
            target=clone/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        def verify():return audit.verify_case('enigma',args.label,'accept',30,terminal,runner)
        assert verify()['editor_passed']
        copied=clone/stage.relative_to(ROOT)
        corruptions=[('S1.BIN',4690,'completed status'),('S1.BIN',3024,'active normal attribute'),
            ('S1.BIN',904,'accepted register bank'),('H1.BIN',14,'quiet UART IER'),
            ('A0.BIN',10,'returned bank proposal'),('TERMINAL.EXE',100,'product identity')]
        rejected=[]
        for leaf,offset,name in corruptions:
            path=copied/leaf;original=path.read_bytes();changed=bytearray(original);changed[offset]^=1;path.write_bytes(changed)
            try:
                try:verify()
                except AssertionError:rejected.append(name)
                else:raise RuntimeError('Auditor accepted corrupted '+name)
            finally:path.write_bytes(original)
        assert verify()['editor_passed']
    result=dict(passed=True,baseline_passes=2,rejected=rejected,label=args.label,
        sources={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__),ROOT/'standalone/record_hook_bbs.py')},
        scope='Copied raw application/BBS evidence only; original artifacts and services are untouched.')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS receipt negative checks:',len(rejected))
if __name__=='__main__':main()
