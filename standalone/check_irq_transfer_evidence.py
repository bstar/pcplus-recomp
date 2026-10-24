#!/usr/bin/env python3
"""Reject corrupted payload, CRC, completion and trace evidence despite pass flags."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

from record_irq_transfers import ROOT,replay,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build')and not out.exists()
    folder=ROOT/'build/bbs-lab/results/enigma/irq7-framed-transfer-02'
    source=ROOT/'build/bbs-lab/irq-framed-server-01/candidate/file_base/pcplus_transfer/PCXTEST.BIN'
    def verify():return replay(folder,source,'PCXTEST.BIN')
    assert json.loads((folder/'result.json').read_text())['passed'];verify()
    protocol=json.loads((folder/'protocol.json').read_text());cases=[]
    path=folder/'RECV/PCXTEST.BIN';data=bytearray(path.read_bytes());data[-1]^=1
    cases.append(('different-stored-byte',path,bytes(data),None))
    path=folder/'display.bin';data=bytearray(path.read_bytes());data[protocol['files'][0]['packets'][0]['offset']]^=1
    cases.append(('corrupted-wire-data-CRC',path,bytes(data),None))
    path=folder/'serial-received.bin';data=bytearray(path.read_bytes())
    for control in protocol['controls']:
        if control['type']==8:data[control['offset']+4]^=1
    cases.append(('missing-valid-receiver-ZFIN',path,bytes(data),None))
    path=folder/'trace.json';data=json.loads(path.read_text());data.insert(0,dict(seconds=0,direction='bbs',offset=0,size=0))
    cases.append(('empty-decoded-byte-event',path,None,json.dumps(data)))
    baseline={str(path.relative_to(ROOT)):sha(path)for _,path,_,_ in cases}
    original_bytes,original_text=Path.read_bytes,Path.read_text;rejected=[]
    for name,target,binary,text in cases:
        def read_bytes(path,*args,**kw):return binary if path.resolve()==target and binary is not None else original_bytes(path,*args,**kw)
        def read_text(path,*args,**kw):return text if path.resolve()==target and text is not None else original_text(path,*args,**kw)
        with patch.object(Path,'read_bytes',read_bytes),patch.object(Path,'read_text',read_text):
            try:verify()
            except AssertionError:rejected.append(dict(case=name,rejected=True))
            else:raise AssertionError('Corruption accepted: '+name)
    assert all(sha(ROOT/name)==digest for name,digest in baseline.items());verify()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(passed=True,cases=rejected,files_unchanged=True,inputs=baseline,
                                  checker_sha256=sha(Path(__file__)),verifier_sha256=sha(ROOT/'standalone/record_irq_transfers.py'),
                                  scope=__doc__),indent=2)+'\n')
    print('PASS four transfer evidence counterexamples; original captures unchanged')


if __name__=='__main__':main()
