#!/usr/bin/env python3
"""Size-probed65,539-byte upload/download pairs in ordinary and maximum layouts.

Separate DOS processes per direction; no same-process reconnect/cancel claim.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from product_inputs import ROOT, select_product, sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--terminal',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build')
    out.mkdir(parents=True,exist_ok=False)
    binary,files=select_product(a.terminal,'TERMINAL.EXE')
    names=['lab/bbs/test_proxy_size_roundtrips.py','lab/bbs/test_proxy_transfer_dos.py',
           'lab/bbs/test_zmodem_dos.py','lab/bbs/audit_proxy_size_transfer.py',
           'lab/bbs/audit_zmodem.py','lab/bbs/synthmodem_proxy_serial.js',
           'lab/bbs/modem.py','lab/bbs/test_transfer_dos.py']
    files += [ROOT/n for n in names]
    frozen={str(n.relative_to(ROOT)):sha(n) for n in files}
    cases=[]
    for rows,hidden in [(25,0),(50,1)]:
        upload_label=out.name+'-upload-'+str(rows)
        name='P'+hashlib.sha256(upload_label.encode()).hexdigest()[:6].upper()+'.BIN'
        for mode in ['upload','download']:
            label=out.name+'-'+mode+'-'+str(rows)
            command=[sys.executable,str(ROOT/'lab/bbs/test_proxy_transfer_dos.py'),
                '--runtime',str(a.runtime.resolve()),'--terminal',str(binary),'--label',label,
                '--mode',mode,'--size-probe','--rows',str(rows),'--hidden',str(hidden),
                '--transfer-wait-ms','60000','--post-menu-reset']
            command += ['--upload-bytes','65539'] if mode=='upload' else ['--download-name',name]
            with (out/(label+'.log')).open('w') as log:
                result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=log,timeout=295)
            assert result.returncode==0,('producer',label)
            audit=out/(label+'-audit')
            with (out/(label+'-audit.log')).open('w') as log:
                result=subprocess.run([sys.executable,str(ROOT/'lab/bbs/audit_proxy_size_transfer.py'),
                    '--label',label,'--output',str(audit)],cwd=ROOT,stdout=log,stderr=log,timeout=30)
            assert result.returncode==0,('audit',label)
            record=json.loads((audit/'result.json').read_text())
            assert record['passed'] and record['payload_bytes']==65539 and record['all256_values']
            assert record['payload_size_lookalikes']>0 and record['NAWS']==[[80,rows-(not hidden)]]
            cases.append(dict(label=label,mode=mode,physical_rows=rows,status_hidden=hidden,
                name=name,payload_sha256=record['payload_sha256'],payload_bytes=65539,
                audit_path=str((audit/'result.json').relative_to(ROOT)),audit_sha256=sha(audit/'result.json'),passed=True))
            print(label,'PASS65,539 bytes',flush=True)
        assert cases[-1]['payload_sha256']==cases[-2]['payload_sha256']
    for n,h in frozen.items():assert sha(ROOT/n)==h,n
    r=dict(passed=True,cases=cases,terminal_sha256=sha(binary),sources=frozen,
        transferred_payload_bytes=262156,scope=__doc__+
        ' Actual paced-keyboard DOS8086 COM3/IRQ5,19200/HARD,synthetic guarded Hayes and staged proxy with real stock Enigma helper/official file metadata. Wire/CRC/finish/menu,raw NAWS,BIOS and exact storage independently audited. No installed service/SIP/DSP/analog/physical or every-layout/protocol acceptance.')
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n')


if __name__=='__main__':main()
