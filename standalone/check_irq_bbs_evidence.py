#!/usr/bin/env python3
"""Reject corrupted BBS IRQ/bank/compiler evidence with pass flags unchanged."""
import argparse
import json
from pathlib import Path
import struct
from unittest.mock import patch

from build_guarded_helper import ROOT, LOOKUP
from record_hook_bbs import verify_case, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    stage = ROOT / 'build/bbs-lab/script-login/irq-bbs-sync5-compact-01'
    output = ROOT / 'build/bbs-lab/results/synchronet/irq-bbs-sync5-compact-01'
    terminal = ROOT / 'build' / (LOOKUP + '-custom-irq') / 'TERMINAL.EXE'
    runner = ROOT / 'build/aspect-register-parent-custom-irq/ASPECT.EXE'
    def verify():
        return verify_case('synchronet',stage.name,'accept',0,terminal,runner,expected_irq=5)
    assert verify()['editor_passed']
    changes = []
    data = bytearray((stage/'H1.BIN').read_bytes());data[26]^=1
    changes.append(('wrong-IRQ5-previous-vector',stage/'H1.BIN',bytes(data),None))
    data = bytearray((stage/'H1.BIN').read_bytes())
    struct.pack_into('<H',data,16,struct.unpack_from('<H',data,16)[0]&~(1<<5))
    changes.append(('unmasked-child-IRQ5',stage/'H1.BIN',bytes(data),None))
    data = bytearray((stage/'B1.BIN').read_bytes());data[0]^=0x80
    changes.append(('wrong-accepted-register-bank',stage/'B1.BIN',bytes(data),None))
    data = bytearray((stage/'LOGON.ASX').read_bytes());data[-1]^=1
    changes.append(('compiled-ASX-changed-with-pass-flags',stage/'LOGON.ASX',bytes(data),None))
    data = json.loads((output/'result.json').read_text());assert data['passed']
    data['serial']['irq']=7
    changes.append(('wrong-reported-physical-IRQ',output/'result.json',None,json.dumps(data)))
    original_bytes, original_text = Path.read_bytes, Path.read_text
    baseline = {str(path.relative_to(ROOT)):sha(path)for _,path,_,_ in changes}
    cases=[]
    for name,target,binary,replacement in changes:
        def read_bytes(path):
            return binary if path.resolve()==target and binary is not None else original_bytes(path)
        def read_text(path,*args,**kwargs):
            return replacement if path.resolve()==target and replacement is not None else original_text(path,*args,**kwargs)
        with patch.object(Path,'read_bytes',read_bytes),patch.object(Path,'read_text',read_text):
            try:
                verify()
            except AssertionError:
                cases.append(dict(case=name,rejected=True))
            else:
                raise AssertionError('Corruption accepted: '+name)
    assert all(sha(ROOT/name)==digest for name,digest in baseline.items())
    assert verify()['editor_passed']
    result=dict(passed=True,cases=cases,files_unchanged=True,
                inputs=baseline,checker_sha256=sha(Path(__file__)),verifier_sha256=sha(ROOT/'standalone/record_hook_bbs.py'),scope=__doc__)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS five evidence counterexamples; files unchanged')


if __name__=='__main__':main()
