#!/usr/bin/env python3
"""Check actual Gateway BBS evidence and copied negative controls."""
import argparse,json,shutil,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from gateway_bbs_support import audit
from product_inputs import sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 capture=a.capture.resolve();out=a.output.resolve();assert capture.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 inputs=['GWVIEW.BIN','GWCHILD.BIN','serial-received.bin'];frozen={n:sha(capture/n) for n in inputs};out.mkdir(parents=True)
 rows=[]
 for name,field in [('unchanged',None),('changed-cell','exact_editor_frame'),('cursor-drift','cursor_and_shape'),('shape-drift','cursor_and_shape'),('missing-mark','observer_complete'),('wrong-mode','mode_and_rows'),('nonempty-tail','actual_empty_tail_child'),('missing-child','actual_empty_tail_child'),('missing-edit-wire','post_return_edit_keys')]:
  folder=out/name;folder.mkdir()
  for n in inputs:shutil.copyfile(capture/n,folder/n)
  report=folder/'GWVIEW.BIN';raw=bytearray(report.read_bytes())
  if name=='changed-cell':raw[24+(len(raw)-24)//2]^=1
  if name=='cursor-drift':raw[14]^=1
  if name=='shape-drift':raw[18]^=1
  if name=='missing-mark':struct.pack_into('<H',raw,4,0)
  if name=='wrong-mode':struct.pack_into('<H',raw,22,0x2813)
  report.write_bytes(raw)
  if name=='nonempty-tail':(folder/'GWCHILD.BIN').write_bytes(b'\1x')
  if name=='missing-child':(folder/'GWCHILD.BIN').unlink()
  if name=='missing-edit-wire':(folder/'serial-received.bin').write_bytes(b'')
  result=audit(folder)
  assert result['passed']==(name=='unchanged'),name
  if field:assert result['checks'][field] is False,(name,result)
  rows.append(dict(case=name,passed=True,rejected=name!='unchanged',intended_check=field))
 assert frozen=={n:sha(capture/n) for n in inputs}
 result=dict(passed=True,capture=str(capture.relative_to(ROOT)),inputs=frozen,cases=rows,sources={n:sha(ROOT/n) for n in ['standalone/check_gateway_bbs_evidence.py','lab/bbs/gateway_bbs_support.py']},scope='Untouched real capture accepted; eight separately copied evidence changes rejected at the intended check. No new DOS run, application modification, corruption recovery or BBS session.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS original evidence and eight copied negative controls')
if __name__=='__main__':main()
