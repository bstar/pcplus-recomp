#!/usr/bin/env python3
"""Check ASPECT wait needles against independent raw Synchronet captures."""
import argparse,hashlib,json,re,sys
from pathlib import Path
from synthmodem_vm_control import ROOT
from synthmodem_synchronet_retry_startup_audio_dos import script,compile_source


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 reference=a.reference.resolve();out=a.output.resolve();assert reference.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 ref=json.loads((reference/'result.json').read_text());assert ref['passed']
 source=script(12345);wire=compile_source(source)
 phases=['login','password','welcome','bulletins','scan','pause','main','files','join','area','upload','upload-name','upload-confirm','description','protocol']
 needles=re.findall(r'^waitfor "([^"]*)"',source,re.M);assert needles.pop(0)=='CONNECT> ' and len(needles)==len(phases)
 cases=[]
 for token,phase in zip(needles,phases):
  raw=(reference/(phase+'.bin')).read_bytes()
  cases.append({'phase':phase,'needle':token,'raw_match_possible':token.encode('ascii') in raw})
 sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 result={'passed':all(c['raw_match_possible'] for c in cases),'cases':cases,'compiled_bytes':len(wire),
  'inputs':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/synthmodem_synchronet_retry_startup_audio_dos.py',reference/'result.json',*[reference/(phase+'.bin') for phase in dict.fromkeys(phases)]]},
  'scope':'Generated ASPECT recipe compiles and every remote wait token is checked against its corresponding independent raw BBS capture. Bridge prompt is outside this peer reference. Missing literal tokens identify fragile/invalid raw-match assumptions; this is neither DOS execution nor audio/native compatibility acceptance.'}
 (out/'SCRIPT.ASP').write_text(source);(out/'SCRIPT.ASX').write_bytes(wire);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':result['passed'],'missing':[c for c in cases if not c['raw_match_possible']]}));return 0 if result['passed'] else 1

if __name__=='__main__':sys.exit(main())
