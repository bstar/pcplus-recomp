#!/usr/bin/env python3
"""Ensure semantic DOS evidence corruptions fail even with updated file hashes."""
import argparse,json,shutil,struct,tempfile
from pathlib import Path
from audit_hangup_retained_carrier_dos import audit
from audit_aspect_transmit_wait import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    source=a.cohort.resolve();audit(source,True);rows=[]
    for kind in ('pause-retired','carrier-not-high','vector-leaked'):
      with tempfile.TemporaryDirectory(prefix='hangup-audit-',dir=ROOT/'build') as temporary:
        folder=Path(temporary)/'cohort';shutil.copytree(source,folder)
        r=json.loads((folder/'checks.json').read_text());row=r['cases'][0];case=folder/row['case']
        if kind=='vector-leaked':
            name='VECNEW.BIN';data=bytearray((case/name).read_bytes());data[0]^=1;(case/name).write_bytes(data)
        else:
            name='RETAIN.BIN';sample=list(struct.unpack('<12H',(case/name).read_bytes()));sample[7 if kind=='pause-retired' else 8]=0
            (case/name).write_bytes(struct.pack('<12H',*sample));row['sample']=sample
        row['captures'][name]=sha(case/name);(folder/'checks.json').write_text(json.dumps(r))
        try:audit(folder,True)
        except AssertionError:rows.append(dict(case=kind,rejected=True))
        else:raise AssertionError('Corrupted evidence admitted: '+kind)
    result=dict(passed=True,cases=rows,checker_sha256=sha(Path(__file__)),cohort_report_sha256=sha(source/'checks.json'),scope=__doc__+' Copies owned evidence into temporary directories; production cohorts remain unchanged.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,rejected=len(rows))))


if __name__=='__main__':main()
