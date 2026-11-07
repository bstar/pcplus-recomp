#!/usr/bin/env python3
"""Reject altered copied journal evidence while preserving the live capture."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from product_inputs import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('capture','bridge','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();cap=a.capture.resolve();bridge=a.bridge.resolve();out=a.output.resolve()
 assert all(p.is_relative_to(ROOT/'build') for p in (cap,bridge,out));out.mkdir(exist_ok=False)
 before={str(p.relative_to(cap)):sha(p) for p in cap.rglob('*') if p.is_file()}
 producer=json.loads((cap/'carrier-checks.json').read_text());assert producer['passed'] and 'lab/bbs/bbs_log_capture.py' in producer['sources']
 cases=[]
 for label in ('unchanged','segment-changed','device-missing','boundary-changed','session-row-dropped'):
  copied=out/label;shutil.copytree(cap,copied)
  if label=='segment-changed':
   p=copied/'server-log-capture/segment-0000.jsonl';data=bytearray(p.read_bytes());assert data;data[0]^=1;p.write_bytes(data)
  elif label=='device-missing':
   p=copied/'server-log-start.json';d=json.loads(p.read_text());del d['device'];p.write_text(json.dumps(d)+'\n')
  elif label=='boundary-changed':
   p=copied/'server-log-capture/result.json';d=json.loads(p.read_text());d['boundary']['prefix_sha256']='0'*64;p.write_text(json.dumps(d)+'\n')
  elif label=='session-row-dropped':
   p=copied/'server-session.jsonl';rows=p.read_bytes().splitlines(keepends=True);assert len(rows)>2;p.write_bytes(b''.join(rows[1:]))
  with (out/(label+'.log')).open('w') as log:
   r=subprocess.run([sys.executable,str(ROOT/'lab/bbs/audit_proxy_carrier.py'),'--capture',str(copied),'--bridge',str(bridge),'--output',str(out/(label+'-audit'))],cwd=ROOT,stdout=log,stderr=log)
  rejected=r.returncode!=0;assert rejected==(label!='unchanged'),label
  cases.append(dict(case=label,passed=True,rejected=rejected,exit_code=r.returncode))
 assert before=={str(p.relative_to(cap)):sha(p) for p in cap.rglob('*') if p.is_file()}
 names=['lab/bbs/check_proxy_carrier_journal_controls.py','lab/bbs/audit_proxy_carrier.py','lab/bbs/bbs_log_capture.py']
 result=dict(passed=True,cases=cases,original_capture_sha256=sha(cap/'carrier-checks.json'),sources={n:sha(ROOT/n) for n in names},scope=__doc__+' One unchanged and four changed copies. Auditor must reject altered segment bytes, missing marker device, mismatched boundary and dropped filtered session row. No live server/proxy/product/capture mutation or new BBS connection.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS carrier journal controls: unchanged accepted,4 altered copies rejected')
if __name__=='__main__':main()
