#!/usr/bin/env python3
"""Reject damaged copies of the carrier-loss/redial evidence."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from product_inputs import ROOT,sha
from check_proxy_cancel_controls import application_positions
from audit_size_probe_screen import telnet


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('capture','bridge','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();cap,bridge,out=[p.resolve() for p in (a.capture,a.bridge,a.output)]
    assert all(p.is_relative_to(ROOT/'build') for p in (cap,bridge,out));out.mkdir(parents=True,exist_ok=False)
    original=json.loads((cap/'carrier-checks.json').read_text());assert original['passed']
    kinds=['unchanged','partial-hash','partial-after-drop','stage-not-clean','missing-carrier-notice',
           'NAWS','hardware','DOS-compiler','second-interrupted','retry-payload']
    cases=[]
    for kind in kinds:
        copied=out/kind/'capture';copied_bridge=out/kind/'bridge'
        shutil.copytree(cap,copied);shutil.copytree(bridge,copied_bridge)
        r=json.loads((copied/'carrier-checks.json').read_text())
        if kind in ('partial-hash','partial-after-drop','stage-not-clean'):
            if kind=='partial-hash':r['snapshots'][0]['sha256']='0'*64
            elif kind=='partial-after-drop':
                first=json.loads((copied/'connection-1/session.json').read_text())
                r['snapshots'][0]['relay_seconds']=first['interrupted_at']+1
            else:r['snapshots'][1]['files']=['PCRX.$$$']
            (copied/'carrier-checks.json').write_text(json.dumps(r)+'\n')
            (copied/'snapshots.json').write_text(json.dumps(r['snapshots'])+'\n')
        elif kind=='missing-carrier-notice':
            path=copied/'LABELS.BIN';data=path.read_bytes();needle='Carrier lost'.encode('cp437')
            cells=b''.join(bytes((c,7)) for c in needle)
            # Preserve every captured attribute, changing only the text cells.
            changed=bytearray(data);found=False
            for i in range(6,len(data)-len(cells)+1,2):
                if data[i:i+len(cells):2]==needle:
                    changed[i:i+len(cells):2]=b' '*len(needle);found=True
            assert found;path.write_bytes(changed)
            r['notices']=[n.replace('Carrier lost',' '*12) for n in r['notices']]
            (copied/'carrier-checks.json').write_text(json.dumps(r)+'\n')
        elif kind=='NAWS':
            path=copied_bridge/'2-telnet-input.bin';data=path.read_bytes()
            old=b'\xff\xfa\x1f\x00P\x00\x18\xff\xf0';assert data.count(old)==1
            path.write_bytes(data.replace(old,b'\xff\xfa\x1f\x00P\x00\x19\xff\xf0',1))
        elif kind in ('hardware','DOS-compiler'):
            path=copied/('AFTER.BIN' if kind=='hardware' else 'program/LOGON.ASX')
            data=bytearray(path.read_bytes());data[0]^=1;path.write_bytes(data)
        elif kind=='second-interrupted':
            path=copied/'connection-2/session.json';s=json.loads(path.read_text());s['interrupted']=True
            path.write_text(json.dumps(s)+'\n')
        elif kind=='retry-payload':
            stream=bytearray((copied/'connection-2/display.bin').read_bytes())
            packet=r['protocol']['files'][0]['packets'][0]
            at=stream.index(ord('A'),packet['offset'],packet['offset']+128)
            raw_path=copied_bridge/'2-telnet-output.bin';raw=bytearray(raw_path.read_bytes());server=telnet(raw)[0]
            start=stream.index(server);assert stream.count(server)==1
            app_at=at-start;positions=application_positions(raw)
            assert raw[positions[app_at]]==65;raw[positions[app_at]]=66;raw_path.write_bytes(raw)
            stream[at]=66
            for path in [copied/'connection-2/display.bin',copied/'connection-2/upstream.bin',copied_bridge/'2-serial-output.bin']:
                assert len(path.read_bytes())==len(stream);path.write_bytes(stream)
        log_path=out/(kind+'.log')
        with log_path.open('w') as log:
            result=subprocess.run([sys.executable,str(ROOT/'lab/bbs/audit_proxy_carrier.py'),
                '--capture',str(copied),'--bridge',str(copied_bridge),'--output',str(out/kind/'audit')],
                cwd=ROOT,stdout=log,stderr=log,timeout=30)
        assert (result.returncode==0)==(kind=='unchanged'),kind
        if kind=='retry-payload':assert 'Data CRC mismatch' in log_path.read_text()
        cases.append(dict(case=kind,rejected=result.returncode!=0,passed=True,log_sha256=sha(log_path)))
        print(kind,'accepted' if result.returncode==0 else 'rejected',flush=True)
    result=dict(passed=True,cases=cases,source_report_sha256=sha(cap/'carrier-checks.json'),
        sources={n:sha(ROOT/n) for n in ['lab/bbs/check_proxy_carrier_controls.py','lab/bbs/audit_proxy_carrier.py','lab/bbs/check_proxy_cancel_controls.py']},
        scope=__doc__+' Ignored copies only. Coherent data mutation preserves raw/proxy/relay equality and is rejected by packet CRC. No DOS execution or live data writes.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
