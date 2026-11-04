#!/usr/bin/env python3
"""Reject altered copies of a real screen-reference capture; never run DOS."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import re
import shutil
from audit_screen_reference import audit,ROOT,sha

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    source=a.capture.resolve();bridge=a.bridge.resolve();out=a.output.resolve()
    assert source.is_relative_to(ROOT/'build') and bridge.is_relative_to(ROOT/'build')
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    accepted=json.loads((source/'screen-reference-audit.json').read_text());assert accepted['passed']
    out.mkdir(parents=True);reports=[]
    kinds=['unchanged','character','attribute','bottom-character','bottom-attribute','cursor','prefix-truncated','unsupported-font']
    if (bridge/'1-proxy-input.bin').exists():kinds.append('proxy-input-truncated')
    for kind in kinds:
        folder=out/kind;capture=folder/'capture';peer=folder/'bridge'
        shutil.copytree(source,capture);shutil.copytree(bridge,peer)
        producer=json.loads((capture/'proxy-integration.json').read_text())
        proof=json.loads((peer/'1-screen-reference.json').read_text())
        if kind in ('character','attribute','bottom-character','bottom-attribute'):
            path=capture/'SCREEN.BIN';data=bytearray(path.read_bytes())
            position=(accepted.get('logical_rows',24)*80-1)*2 if kind.startswith('bottom-') else 0
            if kind.endswith('attribute'):position+=1
            data[position]^=1
            path.write_bytes(data);producer['screen_sha256']=sha(path)
        elif kind=='cursor':
            old=proof['reply'];new=[old[0],old[1]%80+1];proof['reply']=new
            replacement=f'\x1b[{new[0]};{new[1]}R'.encode()
            if 'probeReplyHex' in proof:proof['probeReplyHex']=replacement.hex()
            path=peer/'1-probe-input.bin';data=path.read_bytes()
            altered,count=re.subn(rb'\x1b\[\d+;\d+R',lambda _:replacement,data)
            assert count==1;path.write_bytes(altered)
            path=peer/'1-serial-input.bin';original=path.read_bytes();assert original.endswith(data)
            path.write_bytes(original[:-len(data)]+altered)
        elif kind=='prefix-truncated':
            path=peer/'1-screen-prefix.bin';path.write_bytes(path.read_bytes()[:-1])
        elif kind=='proxy-input-truncated':
            path=peer/'1-proxy-input.bin';path.write_bytes(path.read_bytes()[:-1])
        elif kind=='unsupported-font':
            data=(peer/'1-screen-prefix.bin').read_bytes()
            assert data.count(b'\x1b[0;0 D') in (0,1)
            changed=data.replace(b'\x1b[0;0 D',b'\x1b[0;1 D') if b'\x1b[0;0 D' in data else data[:-4]+b'\x1b[0;1 D'+data[-4:]
            for path in [peer/'1-screen-prefix.bin',peer/'1-serial-output.bin',capture/'serial-sent.bin']:path.write_bytes(changed)
            proof['prefixSha256']=sha(peer/'1-screen-prefix.bin')
            proof['prefixBytes']=len(changed)
        if kind!='unchanged':
            producer['synthetic_audit_control']=kind
            producer['screen_reference']=proof
            (capture/'proxy-integration.json').write_text(json.dumps(producer,indent=2)+'\n')
            (peer/'1-screen-reference.json').write_text(json.dumps(proof,indent=2)+'\n')
        error=None;result=None
        try:
            with contextlib.redirect_stdout(io.StringIO()):result=audit(capture,peer)
        except AssertionError as e:error=str(e)
        rejected=error is not None or not result['passed']
        assert rejected==(kind!='unchanged'),kind
        if kind in ('character','attribute','bottom-character','bottom-attribute'):
            assert result['different_cells']==1 and not result['checks']['all_cells_match']
        if kind=='cursor':assert result['different_cells']==0 and not result['checks']['cursor_matches_reference']
        reports.append(dict(case=kind,passed=True,rejected=rejected,error=error,different_cells=result['different_cells'] if result else None))
        print('PASS',kind,'rejected' if rejected else 'accepted',flush=True)
    report=dict(passed=True,cases=reports,original_capture_sha256=sha(source/'screen-reference-audit.json'),
                sources={n:sha(ROOT/n) for n in ['lab/bbs/check_screen_reference_controls.py','lab/bbs/audit_screen_reference.py','standalone/test_ansi_reference_dos.py']},
                scope=__doc__+' Synthetic counterexamples are declared in copied metadata to exercise cell/cursor comparison beyond hash validation. The positive capture, binaries, fixture server and live services remain unchanged.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
