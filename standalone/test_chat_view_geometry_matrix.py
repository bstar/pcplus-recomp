#!/usr/bin/env python3
"""Real DOS BIOS quarantine matrix plus normal-main saved-preference heights."""
import argparse,concurrent.futures,json,subprocess,sys
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary,out=a.terminal.resolve(),a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 m=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==m['binary_sha256'] and m['chat_loader']['module']['api_version']==0x106
 names=['standalone/test_chat_view_geometry_matrix.py','standalone/test_chat_redisplay_geometry_dos.py','standalone/chat_redisplay_geometry_host.c','standalone/test_chat_redisplay_main_dos.py','standalone/chat_redisplay_watch.asm']
 sources={**m['sources'],**{n:sha(ROOT/n) for n in names}}
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 cases=[]
 def run(case):
  name,script,flags=case;target=out/(out.name+'-'+name)
  with (out/(name+'.log')).open('w') as log:
   r=subprocess.run([sys.executable,str(ROOT/script),'--terminal',str(binary),'--output',str(target),*flags],stdout=log,stderr=log,timeout=150)
  rp=target/'result.json';report=json.loads(rp.read_text()) if rp.exists() else None
  passed=r.returncode==0 and bool(report) and report['passed']
  result=dict(name=name,passed=passed,returncode=r.returncode,receipt=str(rp.relative_to(ROOT)),receipt_sha256=sha(rp) if rp.exists() else None)
  print(name,'PASS' if passed else 'FAIL',flush=True);return result
 for rows in (25,28,43,50):
  for fault in (0,1,2):cases.append(run((f'quarantine-r{rows}-f{fault}','standalone/test_chat_redisplay_geometry_dos.py',['--rows',str(rows),'--fault',str(fault)])))
 maincases=[(f'main-r{r}','standalone/test_chat_redisplay_main_dos.py',['--rows',str(r)]) for r in (25,28,43,50)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:cases+=list(pool.map(run,maincases))
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 result=dict(passed=all(r['passed'] for r in cases),binary_sha256=sha(binary),module_sha256=sha(binary.parent/'PCCHAT.OVL'),cases=cases,sources=sources,original_inputs=[],scope=__doc__+' Twelve explicit BIOS fault/recovery cases use real parent/module entries with supplied initial canonical layout. Four independent normal-main cases use imported PRM display preferences, real BIOS geometry and passive live/visible frame observers. No product instructions/ready flags patched; no physical VGA/modem acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed']
if __name__=='__main__':main()
