#!/usr/bin/env python3
"""Actual DOS shared-key-owner/full-frame diagnostic at25/28/43/50 rows.
Normalized keys supplied by a diagnostic adapter, not BIOS typing. No live serial,
BBS, SIP/DSP/analog or physical acceptance; diagnostic must never be packaged.
"""
import argparse,hashlib,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 m=json.loads((binary.parent/'manifest.json').read_text());assert m['experimental_large_view_frames'] and m['diagnostic_row_geometry_probe'];assert sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 command=[sys.executable,str(ROOT/'standalone/test_display_rows_terminal_dos.py'),'--terminal',str(binary),'--output',str(out/'parent')]
 with (out/'parent.log').open('w') as log:subprocess.run(command,stdout=log,stderr=log,check=True,timeout=90)
 parent=json.loads((out/'parent/result.json').read_text());assert parent['passed'] and parent['diagnostic_package_rejected']
 cases=[];artifacts={}
 for label in ['normal','exclusive']:
  drive=out/'parent'/label/'drive';record=(drive/'VFRAMES.BIN').read_bytes();words=struct.unpack('<115H',record);assert words[:3]==(0x5646,1,16)
  for r,rows in enumerate([25,28,43,50]):
   expected=b''.join(struct.pack('<H',0x0700+65+i%26 if i<rows*80 else 0x5a5a) for i in range(4000))
   for v,key in enumerate([0x2c00,0x8400,0x8300,0x1400]):
    state=words[3+(r*4+v)*7:3+(r*4+v+1)*7];assert state==(rows,key,1,1,1,0,1),state
    opened=(drive/f'LV{r}{v}.BIN').read_bytes();closed=(drive/f'LA{r}{v}.BIN').read_bytes()
    assert len(opened)==len(closed)==8000 and closed==expected
    assert opened!=closed and opened[rows*160:]==expected[rows*160:]
    if v!=1:assert opened[4000:rows*160]==expected[4000:rows*160]
    else:assert b'History is empty.' in opened[(rows-1)*160:rows*160:2]
    cases.append(dict(run=label,rows=rows,key=key,passed=True))
  for leaf in ['VFRAMES.BIN',*[f'L{phase}{r}{v}.BIN' for phase in ['V','A'] for r in range(4) for v in range(4)]]:
   f=drive/leaf;artifacts[str(f.relative_to(ROOT))]=sha(f)
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 report=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),cases=cases,diagnostic_package_rejected=True,parent_result_sha256=sha(out/'parent/result.json'),parent_log_sha256=sha(out/'parent.log'),artifacts=artifacts,checker_inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'standalone/test_display_rows_terminal_dos.py']},scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS actual DOS:32 full-frame view/restore observations, guard tails, row-owner and diagnostic-package rejection')
if __name__=='__main__':main()
