#!/usr/bin/env python3
"""Accept a real listing/editor capture and reject separately copied evidence defects."""
import argparse,json,shutil,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from file_directory_bbs_support import audit
from product_inputs import sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['capture','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();capture=a.capture.resolve();out=a.output.resolve()
 assert capture.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 inputs=['FDVIEW.BIN','serial-received.bin'];frozen={n:sha(capture/n) for n in inputs};out.mkdir(parents=True);cases=[]
 for name,field in [('unchanged',None),('cell','exact_editor_frame'),('cursor','cursor_shape_preserved'),('shape','cursor_shape_preserved'),('missing-listing','observer_complete'),('mode','mode_rows_preserved'),('heading','real_listing_heading'),('filename','real_listing_entry'),('size','real_listing_entry'),('filename-on-wire','file_spec_consumed_locally'),('no-editing','subsequent_edit_keys')]:
  folder=out/name;folder.mkdir()
  for n in inputs:shutil.copyfile(capture/n,folder/n)
  raw=bytearray((folder/'FDVIEW.BIN').read_bytes());wire=(folder/'serial-received.bin').read_bytes()
  if name=='cell':raw[4024]^=1
  elif name=='cursor':raw[14]^=1
  elif name=='shape':raw[18]^=1
  elif name=='missing-listing':struct.pack_into('<H',raw,4,0)
  elif name=='mode':struct.pack_into('<H',raw,22,0x2813)
  elif name=='heading':raw[8024+22*2]^=1
  elif name=='filename':raw[8184+22*2]^=1
  elif name=='size':raw[8184+41*2]^=1
  elif name=='filename-on-wire':wire+=b'TEST.PRM'
  elif name=='no-editing':wire=b''
  (folder/'FDVIEW.BIN').write_bytes(raw);(folder/'serial-received.bin').write_bytes(wire)
  r=audit(folder);assert r['passed']==(field is None),(name,r)
  if field:assert not r['checks'][field],(name,field)
  cases.append(dict(case=name,passed=True,rejected=field is not None,intended_check=field))
 assert frozen=={n:sha(capture/n) for n in inputs}
 result=dict(passed=True,capture=str(capture.relative_to(ROOT)),inputs=frozen,cases=cases,sources={n:sha(ROOT/n) for n in ['standalone/check_file_directory_bbs_evidence.py','lab/bbs/file_directory_bbs_support.py']},scope=__doc__+' Untouched capture accepted; ten independent mutations rejected at their intended check. Copied evidence only; no DOS run or product/BBS modification.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS unchanged capture and ten copied negative controls')
if __name__=='__main__':main()
