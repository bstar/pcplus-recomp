#!/usr/bin/env python3
"""Read-only partial snapshot before completion of the same-call retry."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
from audio_synchronet import ROOT,RUNTIME,snapshot,sha
from audio_synchronet_retry import NAME,RETRY,AREA,payload
from synchronet import ENV

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
 assert out.is_relative_to(ROOT/'build') and out.is_dir();folder=out/'partial-observer';folder.mkdir()
 inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet.py',ROOT/'lab/bbs/audio_synchronet_retry.py',ROOT/'lab/bbs/synchronet.py']}
 before=snapshot();script=folder/'metadata.js';script.write_text("var f=new FileBase('pcplab');if(!f.open())throw Error(f.last_error);print('PARTIAL_JSON:'+JSON.stringify({partial:f.get('"+NAME+"'),retry:f.get('"+RETRY+"')}));f.close();\n")
 deadline=time.monotonic()+900;attempt=0;observations=[]
 while True:
  assert time.monotonic()<deadline,'No official partial observed before deadline'
  if not (AREA/NAME).exists():time.sleep(.5);continue
  attempt+=1;low=time.monotonic_ns();r=subprocess.run([str(RUNTIME/'exec/jsexec'),'-n',str(script)],env=ENV(),capture_output=True,text=True,check=True);high=time.monotonic_ns()
  (folder/f'{attempt:03}.stdout').write_text(r.stdout);(folder/f'{attempt:03}.stderr').write_text(r.stderr)
  value=json.loads(r.stdout.split('PARTIAL_JSON:',1)[1].splitlines()[0]);observations.append(dict(attempt=attempt,before_ns=str(low),after_ns=str(high),value=value))
  assert value['retry'] is None,'Retry already indexed: cannot claim a pre-completion snapshot'
  if value['partial'] is None:time.sleep(.5);continue
  data=(AREA/NAME).read_bytes();st=(AREA/NAME).stat();meta=value['partial']
  assert 0<len(data)<11521 and payload().startswith(data) and meta['size']==len(data) and meta['sha1']==hashlib.sha1(data).hexdigest()
  (folder/'partial.bin').write_bytes(data)
  result=dict(passed=True,partial_bytes=len(data),partial_sha256=sha(folder/'partial.bin'),partial_stat=[st.st_ino,st.st_size,st.st_mtime_ns],
   partial_metadata=meta,retry_metadata_at_observation=None,observations=observations,inputs=inputs,
   server_inputs_preserved=before==snapshot(),inputs_preserved=all(sha(ROOT/n)==h for n,h in inputs.items()),
   captures_sha256={str(p.relative_to(out)):sha(p) for p in folder.iterdir() if p.is_file()},
   scope='Read-only official FileBase snapshot while the same-call retry target is still unindexed. Captures exact cancelled partial bytes/inode/size/mtime and metadata for comparison after retry. No deletion, metadata mutation, product injection or cleanup acceptance.')
  assert result['server_inputs_preserved'] and result['inputs_preserved']
  (out/'partial-observer.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'partial_bytes':len(data),'retry_unindexed':True}));break
