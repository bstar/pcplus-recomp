#!/usr/bin/env python3
"""Keep declared failure flags/hashes consistent while corrupting retained-parser evidence."""
import argparse, json, shutil, struct
from pathlib import Path
import audit_manual_cancel_retained as audit


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('baseline',type=Path); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    out=a.output.resolve(); assert out.is_relative_to(audit.ROOT/'build') and not out.exists(); out.mkdir(parents=True)
    audit.verify(a.baseline.resolve()); rows=[]
    for name in ('first-DCD-high','retained-flow-pause','changed-wire','missing-initialization-error','bad-vector-restore','stock-backend-label'):
        folder=out/name; shutil.copytree(a.baseline.resolve(),folder)
        report=audit.read(folder/'checks.json'); row=next(r for r in report['cases'] if r['case']=='soft')
        target=None
        if name in ('first-DCD-high','retained-flow-pause'):
            target=folder/'soft/CANCEL.BIN'; data=bytearray(target.read_bytes())
            struct.pack_into('<H',data,8 if name=='first-DCD-high' else 16,1); target.write_bytes(data)
        elif name=='changed-wire':
            target=folder/'soft/serial.bin'; target.write_bytes(target.read_bytes().replace(b'AATZ',b'ATZ',1))
        elif name=='missing-initialization-error':
            target=folder/'soft/peer-events.json'; events=audit.read(target)
            events=[e for e in events if e['kind']!='initialization-ERROR']; target.write_text(json.dumps(events))
        elif name=='bad-vector-restore':
            target=folder/'soft/VECNEW.BIN'; data=bytearray(target.read_bytes()); data[0]^=1; target.write_bytes(data)
        else: report['emulator']['test_backend']=False
        if target: row['captures'][target.name]=audit.sha(target)
        (folder/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
        receipt=audit.read(folder/'retained-checks.json'); receipt['producer_report_sha256']=audit.sha(folder/'checks.json')
        receipt['cases'][0]['capture_sha256']=row['captures']
        (folder/'retained-checks.json').write_text(json.dumps(receipt,indent=2)+'\n')
        try: audit.verify(folder)
        except AssertionError: rows.append(dict(case=name,rejected=True,producer_declared_failure_preserved=True,changed_hashes_updated=True))
        else: raise AssertionError('Accepted corrupt evidence: '+name)
    result=dict(passed=True,cases=rows,auditor_sha256=audit.sha(Path(audit.__file__)),checker_sha256=audit.sha(Path(__file__)))
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(dict(passed=True,rejected=len(rows))))


if __name__=='__main__': main()
