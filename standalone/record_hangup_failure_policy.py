#!/usr/bin/env python3
"""Bind old/new DOS failed-hangup, recovery and source-built regression evidence."""
import argparse,json,struct
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha,read
from audit_hangup_retained_carrier_dos import audit
from audit_manual_reconnect import verify


def recovery(folder,parent):
    r=read(folder/'checks.json');assert r['passed'] and r['parent_sha256']==parent
    assert len(r['cases'])==2 and {v['case'] for v in r['cases']}=={'drop0-both','drop1-both'}
    for name,digest in r['inputs'].items():assert sha(folder/'inputs'/name)==digest
    for row in r['cases']:
        case=folder/row['case'];assert row['passed'] and all(row['checks'].values())
        for name,digest in row['captures'].items():assert sha(case/name)==digest
        events=read(case/'peer-events.json');assert all(x['time']<=y['time'] for x,y in zip(events,events[1:]))
        wire=bytearray();escaped=False
        for e in events:
            if e['kind']!='transport-receive':continue
            for value in bytes.fromhex(e['hex']):
                if escaped:
                    escaped=False
                    if value!=255:continue
                elif value==255:escaped=True;continue
                wire.append(value)
        assert not escaped and wire==(case/'serial.bin').read_bytes()
        reply=b'\x1b[1;16R\x1b[?62;2c';dial=b'ATZ\rATDCaseTest:23\r'
        assert bytes(wire)==dial+reply+b'arm+++ATH\r'+dial+reply+b'ready\x1b[1;16R+++ATH\r'
        connected=[e for e in events if e['kind']=='online-CONNECT'];off=[e for e in events if e['kind']=='hangup-command-disconnect']
        xoff=[e for e in events if e['kind']=='XOFF-online'];xon=[e for e in events if e['kind']=='XON-recovery']
        assert len(connected)==len(off)==2 and len(xoff)==len(xon)==1
        assert connected[0]['time']<xoff[0]['time']<xon[0]['time']<off[0]['time']<connected[1]['time']<off[1]['time']
        assert xon[0]['time']-xoff[0]['time']>=5.8
        assert sum(e['kind']=='reconnected-query' for e in events)==1
        sample=struct.unpack('<12H',(case/'RETAIN.BIN').read_bytes())
        assert sample[0]==0x4847 and sample[3]>4 and sample[6]>4 and sample[7]==0 and sample[8]>4 and sample[9]==8 and sample[11]==1
        assert (sample[5]>8 if row['case'].startswith('drop1') else sample[5]==0)
        assert (case/'BEFORE.BIN').read_bytes()==(case/'AFTER.BIN').read_bytes() and (case/'BEFORE.BIN').stat().st_size==42
        assert (case/'VECOLD.BIN').read_bytes()==(case/'VECNEW.BIN').read_bytes() and (case/'VECOLD.BIN').stat().st_size==8
        assert sha(case/'TERMINAL.EXE')==parent
    return r


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ('baseline','fixed','recovery','regressions','stock-reconnect','output'):p.add_argument('--'+flag,type=Path,required=True)
    a=p.parse_args();old=audit(a.baseline.resolve());fixed=audit(a.fixed.resolve(),True);parent=fixed['parent_sha256']
    assert old['parent_sha256']!=parent
    rec=recovery(a.recovery.resolve(),parent);stock,stock_rows=verify(a.stock_reconnect.resolve(),False);assert stock['parent_sha256']==parent
    reg=a.regressions.resolve();proof=read(reg/'source-proof/result.json');assert proof['passed'] and proof['products']['terminal']==parent and proof['original_inputs']==[]
    reports={}
    for name in ('hangup-normal.json','hangup-mouse.json','resync-normal.json','resync-mouse.json','carrier-normal/checks.json','carrier-mouse/checks.json','connection-checks.json','manual-reconnect/checks.json','stock/build/connection-dos/result.json'):
        r=read(reg/name);assert r['passed'];reports[name]=dict(sha256=sha(reg/name),case_count=len(r['cases']))
        expected=proof['products']['terminal-mouse' if 'mouse' in name else 'terminal']
        assert r.get('parent_sha256',r.get('binary_sha256'))==expected
        assert all(v['passed'] for v in r['cases'])
        if name.startswith('hangup-'):assert len(r['cases'])==23
    for name,digest in proof['sources'].items():assert sha(ROOT/name)==digest and sha(reg/'source-proof/source'/name)==digest
    for name,digest in proof['products'].items():
        assert sha(ROOT/'build'/name/'TERMINAL.EXE')==digest
        manifest=read(ROOT/'build'/name/'manifest.json');assert manifest['binary_sha256']==digest
    assert reports['stock/build/connection-dos/result.json']['case_count']==5
    result=dict(passed=True,retained_carrier_hangup_policy_accepted=True,full_F03_accepted=False,physical_hardware_accepted=False,
        baseline_parent_sha256=old['parent_sha256'],current_products=proof['products'],
        DOS_baseline=dict(cohort=str(a.baseline),report_sha256=sha(a.baseline/'checks.json'),cases=4),
        DOS_fixed=dict(cohort=str(a.fixed),report_sha256=sha(a.fixed/'checks.json'),cases=4,audit_sha256=sha(a.fixed/'audit.json')),
        DOS_recovery=dict(cohort=str(a.recovery),report_sha256=sha(a.recovery/'checks.json'),cases=2,cases_evidence=rec['cases']),
        stock_manual_reconnect=dict(cohort=str(a.stock_reconnect),report_sha256=sha(a.stock_reconnect/'checks.json'),cases=stock_rows),
        regressions=reports,source_proof=dict(report_sha256=sha(reg/'source-proof/result.json'),source_files=len(proof['sources']),products=2,original_inputs=[]),
        source_inputs=fixed['inputs'],emulator=fixed['emulator'],auditor_sha256=sha(Path(__file__)),
        scope='Selected failed-hangup correction only. Actual8086 DOS old/new retained-online peer, XON/Alt-H recovery/redial/manual query, stock modem DTR reconnect and ordinary stock modem cases; linked normal/mouse checks and source-only reproduction. Startup/successful always-high DCD initialization policy unchanged. Exiting releases DOS ownership even if modem retains carrier. Actual Boca/SPA2102, other modem policies/pressure, current-parent BBS/audio and full application remain open.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,DOS_fixed=4,DOS_recovery=2,stock_reconnect=2,linked_policy=46,source_products=2)))


if __name__=='__main__':main()
