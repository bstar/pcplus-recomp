#!/usr/bin/env python3
"""Compare actual source/original DOS help VGA frames on declared workflows."""
import argparse,json,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha

CASES={
 'topics-cancel':([84,27,27],1),
 'scroll':([0x5000,0x5100,0x4800,0x4900,0x4f00,0x4700,27],1),
 'topic-memory':([84,0x4f00,13,84,0x4800,0x4900,0x5100,0x4700,13,27],1),
 'search-no':([83,76,73,78,69,32,48,53,13,67,78,27],1),
 'search-yes':([83,76,73,78,69,32,48,53,13,67,89,27],1),
 'search-cancel':([83,65,66,8,27,27],1),
 'search-other-topic':([83,84,79,80,73,67,32,52,54,13,89,27],1),
 'search-missing':([83,78,69,86,69,82,13,89,27,27],1),
 'negative-context':([27],0xffff),
}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 build=a.build.resolve();original=a.original.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 assert sha(original)=='5d135afc5808ddec923ec027f385490c7ecd4fa5004d11cefe6ff4a3c468d0aa'
 manifest=json.loads((build/'manifest.json').read_text())
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 for name,digest in manifest['products'].items():assert sha(build/name)==digest,name
 pairs=[];all_equal=True
 for rows in (25,50):
  for label,(keys,topic) in CASES.items():
   reports=[]
   for variant,helper in [('original',original),('source',build/'PCHELP.RTE')]:
    dest=out/(str(rows)+'-'+label+'-'+variant)
    with (out/(dest.name+'.log')).open('w') as log:
     subprocess.run([sys.executable,str(ROOT/'standalone/capture_help_screen.py'),'--helper',str(helper),'--output',str(dest),'--rows',str(rows),'--keys',json.dumps(keys),'--topic',str(topic)],stdout=log,stderr=log,check=True)
    reports.append(json.loads((dest/'result.json').read_text()))
   left=out/(str(rows)+'-'+label+'-original');right=out/(str(rows)+'-'+label+'-source')
   differences=[]
   for n in range(max(reports[0]['captures'],reports[1]['captures'])):
    name='VIEW%02d.BIN'%n;l=left/name;r=right/name
    if not l.exists() or not r.exists():differences.append(dict(frame=n,missing=True));continue
    lb=l.read_bytes()[:rows*160];rb=r.read_bytes()[:rows*160]
    diff=[dict(row=i//160,column=i%160//2,attribute=bool(i%2),original=x,source=y) for i,(x,y) in enumerate(zip(lb,rb)) if x!=y]
    if diff:differences.append(dict(frame=n,count=len(diff),first=diff[:12]))
   equal=not differences and reports[1]['child_exit_code']==0 and reports[0]['restored'] and reports[1]['restored'] and reports[0]['metadata']==reports[1]['metadata']
   pairs.append(dict(rows=rows,case=label,passed=equal,original=reports[0],source=reports[1],differences=differences))
   all_equal=all_equal and equal;print(rows,label,'PASS' if equal else 'FAIL',len(differences),flush=True)
 report=dict(passed=all_equal,pairs=pairs,source_manifest_sha256=sha(build/'manifest.json'),checker_sha256=sha(Path(__file__)),capture_checker_sha256=sha(ROOT/'standalone/capture_help_screen.py'),scope='Actual original/source DOS helper runs, authored LF HLP, identical legacy producer/BIOS observer. All visible VGA bytes and attributes compared at each scripted keyboard read. Native original child exit byte recorded separately. No synthetic analysis executable, terminal integration, arbitrary input/fault/mouse or physical acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if all_equal else 1

if __name__=='__main__':raise SystemExit(main())
