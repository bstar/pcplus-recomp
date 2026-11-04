#!/usr/bin/env python3
"""Reject declared corruptions of copied transfer artifacts; no DOS or BBS writes."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from product_inputs import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build')
    out.mkdir(parents=True,exist_ok=False)
    lab=ROOT/'build/bbs-lab';source=lab/(a.label+'-transfer')
    capture=lab/'results/enigma'/a.label;bridge=lab/(a.label+'-proxy')
    report=json.loads((source/'result.json').read_text())
    assert report['passed'] and report['mode']=='upload' and report['fixture']['bytes']==65539
    kinds=['unchanged','NAWS','owned-prefix','payload-CRC','BIOS-font','official-size','wrong-storage','hardware','truncated-proxy-output']
    cases=[]
    for kind in kinds:
        label=out.name+'-'+kind.lower()
        copied=lab/(label+'-transfer');copied_capture=lab/'results/enigma'/label;copied_bridge=lab/(label+'-proxy')
        for original,target in [(source,copied),(capture,copied_capture),(bridge,copied_bridge)]:
            assert not target.exists();shutil.copytree(original,target)
        if kind=='NAWS':
            path=copied_bridge/'1-telnet-input.bin';data=path.read_bytes();old=b'\xff\xfa\x1f\x00P\x00\x18\xff\xf0';assert data.count(old)==1
            path.write_bytes(data.replace(old,b'\xff\xfa\x1f\x00P\x00\x19\xff\xf0',1))
        elif kind=='owned-prefix':
            path=copied_bridge/'1-serial-input.bin';data=path.read_bytes();assert data.startswith(b'loc\r\x1b[8;24;80t')
            path.write_bytes(b'loc\r\x1b[8;25;80t'+data[len(b'loc\r\x1b[8;24;80t'):])
        elif kind=='payload-CRC':
            protocol=json.loads((copied_capture/'protocol.json').read_text());at=protocol['files'][0]['packets'][0]['offset']
            path=copied_capture/'serial-received.bin';data=bytearray(path.read_bytes());data[at]^=1;path.write_bytes(data)
        elif kind=='BIOS-font':
            path=copied_capture/'GEOM.BIN';data=bytearray(path.read_bytes());data[2]^=1;path.write_bytes(data)
        elif kind in ('official-size','wrong-storage'):
            path=copied_capture/'server-audit.stdout';data=json.loads(path.read_text())
            if kind=='official-size':data['entries'][0]['meta']['byte_size']=65538
            else:data['entries'][0]['filePath']=str(ROOT/'build/bbs-lab/enigma/source/file_base/pcplus_transfer/PCXTEST.BIN')
            path.write_text(json.dumps(data)+'\n')
        elif kind=='hardware':
            path=copied_capture/'AFTER.BIN';data=bytearray(path.read_bytes());data[0]^=1;path.write_bytes(data)
        elif kind=='truncated-proxy-output':
            path=copied_bridge/'1-serial-output.bin';path.write_bytes(path.read_bytes()[:-1])
        destination=out/kind
        with (out/(kind+'.log')).open('w') as log:
            code=subprocess.run([sys.executable,str(ROOT/'lab/bbs/audit_proxy_size_transfer.py'),
                '--label',label,'--output',str(destination)],cwd=ROOT,stdout=log,stderr=log,timeout=30).returncode
        assert (code==0)==(kind=='unchanged'),kind
        cases.append(dict(case=kind,rejected=code!=0,passed=True,log_sha256=sha(out/(kind+'.log'))))
        print(kind,'accepted' if code==0 else 'rejected',flush=True)
    r=dict(passed=True,cases=cases,source_wrapper_sha256=sha(source/'result.json'),
        sources={name:sha(ROOT/name) for name in ['lab/bbs/check_proxy_size_transfer_controls.py','lab/bbs/audit_proxy_size_transfer.py']},
        scope=__doc__+' Copies preserve real protocol/chronology; only declared fields mutate. Wrong-storage redirects copied metadata to an existing different owned fixture read-only. Original captures/source payload/live catalog/destination unchanged.')
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n')


if __name__=='__main__':main()
