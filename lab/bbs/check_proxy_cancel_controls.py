#!/usr/bin/env python3
"""Reject copied cancellation artifacts, including coherent payload corruption."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from product_inputs import ROOT,sha
from audit_size_probe_screen import telnet
from test_transfer_dos import timestamp


def application_positions(raw):
    positions=[];i=0
    while i<len(raw):
        if raw[i]!=255:positions.append(i);i+=1;continue
        command=raw[i+1]
        if command==255:positions.append(i);i+=2
        elif command in (251,252,253,254):i+=3
        else:
            assert command==250;i+=2
            while True:
                if raw[i]!=255:i+=1;continue
                if raw[i+1]==255:i+=2;continue
                assert raw[i+1]==240;i+=2;break
    assert bytes(raw[p] for p in positions)==telnet(raw)[0]
    return positions


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['capture','bridge','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();cap,bridge,out=[p.resolve() for p in (a.capture,a.bridge,a.output)]
    assert all(p.is_relative_to(ROOT/'build') for p in (cap,bridge,out));out.mkdir(parents=True,exist_ok=False)
    original=json.loads((cap/'cancel-checks.json').read_text());assert original['passed']
    kinds=['unchanged','partial-hash','partial-after-cancel','stage-not-clean','BIOS-Escape','NAWS','hardware','extra-session','retry-payload']
    cases=[]
    for kind in kinds:
        copied=out/kind/'capture';copied_bridge=out/kind/'bridge';shutil.copytree(cap,copied);shutil.copytree(bridge,copied_bridge)
        r=json.loads((copied/'cancel-checks.json').read_text())
        if kind in ('partial-hash','partial-after-cancel','stage-not-clean'):
            partial=next(s for s in r['snapshots'] if s['kind']=='partial')
            if kind=='partial-hash':partial['sha256']='0'*64
            elif kind=='partial-after-cancel':
                keys=(copied/'serial-received.bin').read_bytes();trace=json.loads((copied/'trace.json').read_text())
                partial['seconds']=timestamp(trace,'dos',keys.index(b'\x18'*8+b'\x08'*10))+1
            else:next(s for s in r['snapshots'] if s['kind']=='after-cancel-before-retry')['files']={'PCRX.$$$':'0'*64}
            (copied/'cancel-checks.json').write_text(json.dumps(r)+'\n');(copied/'cancel-snapshots.json').write_text(json.dumps(r['snapshots'])+'\n')
        elif kind=='BIOS-Escape':
            path=copied/'LABELS.BIN';data=bytearray(path.read_bytes());data[5]&=0x7f;path.write_bytes(data)
        elif kind=='NAWS':
            path=copied_bridge/'1-telnet-input.bin';data=path.read_bytes();old=b'\xff\xfa\x1f\x00P\x00\x18\xff\xf0';assert data.count(old)==1
            path.write_bytes(data.replace(old,b'\xff\xfa\x1f\x00P\x00\x19\xff\xf0',1))
        elif kind=='hardware':
            path=copied/'AFTER.BIN';data=bytearray(path.read_bytes());data[0]^=1;path.write_bytes(data)
        elif kind=='extra-session':
            path=copied/'server-session.jsonl';rows=path.read_text().splitlines();row=json.loads(rows[0]);row['sessionId']='negative-extra-session'
            path.write_text('\n'.join(rows+[json.dumps(row)])+'\n')
        elif kind=='retry-payload':
            # Mutate the same ASCII payload byte in captured server application
            # and raw TCP, preserving IAC decoding and observer/proxy equality.
            stream=bytearray((copied/'display.bin').read_bytes());packet=r['protocol']['retry']['files'][0]['packets'][0]
            at=stream.index(ord('A'),packet['offset'],packet['offset']+128);assert stream[at]==65
            raw_path=copied_bridge/'1-telnet-output.bin';raw=bytearray(raw_path.read_bytes());server=telnet(raw)[0]
            assert stream.endswith(server);app_at=at-(len(stream)-len(server));positions=application_positions(raw)
            assert raw[positions[app_at]]==65;raw[positions[app_at]]=66;raw_path.write_bytes(raw)
            stream[at]=66
            for path in [copied/'display.bin',copied/'bbs-wire.bin',copied/'serial-sent.bin',copied_bridge/'1-serial-output.bin']:
                assert len(path.read_bytes())==len(stream);path.write_bytes(stream)
        destination=out/kind/'audit';log_path=out/(kind+'.log')
        with log_path.open('w') as log:
            result=subprocess.run([sys.executable,str(ROOT/'lab/bbs/audit_proxy_cancel_retry.py'),
                '--capture',str(copied),'--bridge',str(copied_bridge),'--output',str(destination)],
                cwd=ROOT,stdout=log,stderr=log,timeout=30)
        assert (result.returncode==0)==(kind=='unchanged'),kind
        cases.append(dict(case=kind,rejected=result.returncode!=0,passed=True,log_sha256=sha(log_path)))
        print(kind,'accepted' if result.returncode==0 else 'rejected',flush=True)
    result=dict(passed=True,cases=cases,source_report_sha256=sha(cap/'cancel-checks.json'),
        sources={n:sha(ROOT/n) for n in ['lab/bbs/check_proxy_cancel_controls.py','lab/bbs/audit_proxy_cancel_retry.py']},
        scope=__doc__+' Only ignored copies change. Coherent payload case preserves proxy/observer/raw-Telnet equality, then requires independent packet integrity rejection. No DOS execution,live BBS catalog or source payload writes.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
