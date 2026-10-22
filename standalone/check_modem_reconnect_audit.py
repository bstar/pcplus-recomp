#!/usr/bin/env python3
"""Corrupt owned copies while keeping producer checks green and hashes current."""
import argparse,json,shutil,struct
from pathlib import Path
from audit_modem_reconnect import ROOT,sha,read,verify


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','fixed','output','receipt'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();receipt=a.receipt.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    assert receipt.is_relative_to(ROOT/'docs/validation') and not receipt.exists()
    out.mkdir(parents=True);rows=[]
    verify(a.baseline.resolve(),True);verify(a.fixed.resolve(),False)
    for name,gap in [('dirty-fixed-command',False),('erased-baseline-error',True),('wrong-child-exit',False),
                     ('wrong-hardware',False),('wrong-second-script',False),('wrong-call-count',False),
                     ('missing-second-socket',False),('wrong-manual-reply',False)]:
        folder=out/name;shutil.copytree(a.baseline if gap else a.fixed,folder)
        case=folder/'soft';report=read(folder/'checks.json');row=next(r for r in report['cases'] if r['case']=='soft')
        changed=[]
        def write(leaf,data):
            (case/leaf).write_bytes(data);row['captures'][leaf]=sha(case/leaf);changed.append(leaf)
        if name=='dirty-fixed-command':
            log=(case/'dosbox.log').read_bytes();needle=b'Command sent to modem: ->ATZ<-'
            assert log.count(needle)==2;at=log.rfind(needle)
            write('dosbox.log',log[:at]+log[at:].replace(needle,b'Command sent to modem: ->\x13\x11ATZ<-',1))
        elif name=='erased-baseline-error':
            log=(case/'dosbox.log').read_bytes();assert b'Modem response: ERROR' in log
            write('dosbox.log',log.replace(b'Modem response: ERROR',b'Modem response: OK'))
        elif name=='wrong-child-exit':
            raw=bytearray((case/'RENDER.BIN').read_bytes());struct.pack_into('<H',raw,12,0);write('RENDER.BIN',bytes(raw))
        elif name=='wrong-hardware':
            raw=bytearray((case/'AFTER.BIN').read_bytes());raw[0]^=1;write('AFTER.BIN',bytes(raw))
        elif name=='wrong-second-script':write('SECOND.OK',b'BAD')
        elif name=='wrong-call-count':
            raw=bytearray((case/'TEST.DIR').read_bytes());at=250+61+9
            struct.pack_into('<H',raw,at,(struct.unpack_from('<H',raw,at)[0]+1)&65535);write('TEST.DIR',bytes(raw))
        elif name=='missing-second-socket':
            events=read(case/'peer-events.json')
            for e in events:
                if e['kind']=='connected' and e['session']==2:e['session']=1
            write('peer-events.json',(json.dumps(events,indent=2)+'\n').encode())
        else:
            # Alter the complete decoded wire and matching peer fragments so
            # custody and stream equality pass; the declared CPR must still fail.
            wire=(case/'serial.bin').read_bytes();assert b'\x1b[1;25R' in wire
            wire=wire.replace(b'\x1b[1;25R',b'\x1b[1;24R');write('serial.bin',wire)
            events=read(case/'peer-events.json');cursor=0
            for e in events:
                if e['kind']=='receive':
                    n=len(bytes.fromhex(e['hex']));e['hex']=wire[cursor:cursor+n].hex();cursor+=n
            assert cursor==len(wire)
            write('peer-events.json',(json.dumps(events,indent=2)+'\n').encode())
        assert report['passed'] and all(c['passed'] and all(c['checks'].values()) for c in report['cases'])
        (folder/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
        rejected=False
        try:verify(folder,gap)
        except AssertionError:rejected=True
        assert rejected,name
        rows.append(dict(case=name,rejected=True,producer_checks_still_passed=True,updated_capture_hashes=changed))
    (out/'checks.json').write_text(json.dumps(dict(passed=True,cases=rows),indent=2)+'\n')
    result=dict(passed=True,cases=rows,auditor_sha256=sha(ROOT/'standalone/audit_modem_reconnect.py'),
                checker_sha256=sha(Path(__file__)),baseline_sha256=sha(a.baseline/'checks.json'),fixed_sha256=sha(a.fixed/'checks.json'),
                cohort=str(out.relative_to(ROOT)),scope=__doc__+' Eight semantic alterations are rejected independently of producer booleans/capture checksums. Baseline/fixed valid controls pass. No product executable is changed.')
    receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,rejected=len(rows))))


if __name__=='__main__':main()
