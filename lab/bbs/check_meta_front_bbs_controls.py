#!/usr/bin/env python3
"""Reject damaged copied Meta/editor evidence without altering the live capture."""
import argparse,json
from pathlib import Path
from meta_front_bbs_support import ROOT,audit,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('capture','terminal','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();capture=a.capture.resolve();out=a.output.resolve();binary=a.terminal.resolve()
 assert capture.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 raw=(capture/'METAVIEW.BIN').read_bytes();wire=(capture/'serial-received.bin').read_bytes();original={n:sha(capture/n)for n in ('METAVIEW.BIN','serial-received.bin')}
 cases=[]
 for name,offset in [('unchanged',None),('character',4024+80),('attribute',4024+81),('cursor',14),('shape',18),('heading',8024+522),('definition',8024+1010),('incomplete-observer',2),('truncated',-1),('local-keystroke-leak',-2)]:
  folder=out/name;folder.mkdir();data=bytearray(raw);tx=wire
  if offset==-1:data=data[:-1]
  elif offset==-2:tx+=b'ZZZ'
  elif offset is not None:data[offset]^=1
  (folder/'METAVIEW.BIN').write_bytes(data);(folder/'serial-received.bin').write_bytes(tx)
  v=audit(folder,binary);assert v['passed']==(name=='unchanged'),name
  cases.append(dict(case=name,rejected=not v['passed'],failed_checks=[k for k,v in v['checks'].items()if not v]))
 assert original=={n:sha(capture/n)for n in original}
 r=dict(passed=True,cases=cases,capture_inputs=original,binary_sha256=sha(binary),sources={n:sha(ROOT/n)for n in ('lab/bbs/check_meta_front_bbs_controls.py','lab/bbs/meta_front_bbs_support.py')},scope='Read-only original evidence; isolated copies mutate one frame, cursor, heading, definition, observer completion or local-wire property. No live server or application mutation.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS Meta editor copied-evidence controls:',len(cases))
if __name__=='__main__':main()
