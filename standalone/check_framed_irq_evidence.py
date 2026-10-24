#!/usr/bin/env python3
"""Reject forged isolated-server identity, buffering, IRQ and decoder evidence."""
import argparse
import json
from pathlib import Path
import struct
from unittest.mock import patch

from build_guarded_helper import ROOT,LOOKUP
from record_hook_bbs import verify_case,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build')and not out.exists()
    stage=ROOT/'build/bbs-lab/script-login/irq-framed-candidate7-01'
    output=ROOT/'build/bbs-lab/results/enigma/irq-framed-candidate7-01'
    candidate=ROOT/'build/bbs-lab/irq-framed-server-01/candidate'
    terminal=ROOT/'build'/(LOOKUP+'-custom-irq')/'TERMINAL.EXE'
    runner=ROOT/'build/aspect-register-parent-custom-irq/ASPECT.EXE'
    def verify():return verify_case('enigma',stage.name,'accept',0,terminal,runner,
                                   expected_irq=7,server_instance=candidate)
    assert verify()['editor_passed']
    cases=[]
    path=stage/'checks.json';data=json.loads(path.read_text());assert data['passed']
    data['server_fixture']['root']='build/bbs-lab/enigma/source'
    cases.append(('stock-disguised-as-selected-candidate',path,None,json.dumps(data)))
    path=output/'result.json';data=json.loads(path.read_text());assert data['passed']
    data['modem_packet_delay_ms']=30
    cases.append(('buffered-disguised-as-immediate',path,None,json.dumps(data)))
    path=stage/'H1.BIN';data=bytearray(path.read_bytes())
    struct.pack_into('<H',data,16,struct.unpack_from('<H',data,16)[0]&~128)
    cases.append(('unmasked-IRQ7',path,bytes(data),None))
    path=candidate/'core/key_stream.js'
    cases.append(('different-decoder-source',path,path.read_bytes()+b'\n',None))
    baseline={str(path.relative_to(ROOT)):sha(path)for _,path,_,_ in cases}
    original_bytes,original_text=Path.read_bytes,Path.read_text
    rejected=[]
    for name,target,binary,text in cases:
        def read_bytes(path,*args,**kw):
            return binary if path.resolve()==target and binary is not None else original_bytes(path,*args,**kw)
        def read_text(path,*args,**kw):
            return text if path.resolve()==target and text is not None else original_text(path,*args,**kw)
        with patch.object(Path,'read_bytes',read_bytes),patch.object(Path,'read_text',read_text):
            try:verify()
            except AssertionError:rejected.append(dict(case=name,rejected=True))
            else:raise AssertionError('Corruption accepted: '+name)
    assert all(sha(ROOT/name)==digest for name,digest in baseline.items())and verify()['editor_passed']
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(passed=True,cases=rejected,files_unchanged=True,inputs=baseline,
                                  checker_sha256=sha(Path(__file__)),verifier_sha256=sha(ROOT/'standalone/record_hook_bbs.py'),
                                  scope=__doc__),indent=2)+'\n')
    print('PASS four isolated-server evidence counterexamples; files unchanged')


if __name__=='__main__':main()
