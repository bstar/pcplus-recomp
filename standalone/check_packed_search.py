#!/usr/bin/env python3
"""Check packed search selections against the unchanged original source-parent algorithm."""
import argparse,json
from pathlib import Path
from check_packed_command_ui import Menu
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['plain','packed','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();plain=a.plain.resolve();packed=a.packed.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 assert sha(plain)=='93f08d0cf3fd4174718e7ca727758ddb63f4e6f0ecd1471b3fb00c41c1f4d800'
 m=json.loads(packed.with_name('manifest.json').read_text());assert sha(packed)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 old,new=Menu(plain),Menu(packed);cases=[]
 for query in ['editor','Alt-A','interval','recording','return to',' DOS ','     Alt','A'*31,'zzzzzzzz','Send','Enter','PCPLUS']:
  for menu in [old,new]:
   menu.event(0,ord('`'));menu.event(1,ord('/'))
   for c in query:menu.event(1,ord(c))
  before=old.event(1,13);after=new.event(1,13)
  assert before[0]==after[0] and before[2:]==after[2:]
  no_match=b'No matching topic' in after[1][::2]
  assert (b'No matching topic' in before[1][::2])==no_match,query
  label=None
  if not no_match:
   # The old category conversion can leave unrelated suffix cells. Compare
   # the complete selected label, which both actual search owners paint last.
   label=after[1][804:960:2].rstrip(b' ')
   assert label and before[1][804:804+len(label)*2:2]==label,query
  cases.append(dict(query=query,no_match=no_match,label=label.decode('cp437') if label else None,passed=True))
 result=dict(passed=True,binary_sha256=sha(packed),reference_sha256=sha(plain),cases=cases,
  sources={n:sha(ROOT/n) for n in ['standalone/check_packed_search.py','standalone/check_packed_command_ui.py','standalone/dos_image.py']},
  scope=__doc__+' Actual linked legacy naive search versus packed rolling-window search. Compare complete selected labels or no-match,return and owner/action states. Known old category corruption is excluded explicitly; full-frame equality uses the separately corrected uncompressed control.')
 out.mkdir();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'legacy search selection/no-match controls')
if __name__=='__main__':main()
