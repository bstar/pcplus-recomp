#!/usr/bin/env python3
"""Production DOS redisplay exports, independent video observer and real files."""
import hashlib,json,struct,subprocess
from pathlib import Path
from test_connection_dos import run,ROOT,BINARY
def main():
 out=ROOT/'build/history-export-dos';out.mkdir(parents=True,exist_ok=True)
 observer=out/'RVWATCH.COM'
 subprocess.run(['nasm','-f','bin',str(ROOT/'standalone/redisplay_watch.asm'),'-o',str(observer)],check=True)
 lines=b''.join(f'HIST{i:03d} exact history'.encode()+b'\r\n' for i in range(40))
 banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c\r\n'+lines+b'\x1b[2J\x1b[HFIRST BYTE SAFE'
 cases=[]
 for name,prefix,repeat in [('history-create',b'',1),('history-append-repeat',b'PREFIX\0\x1a'+b'X'*70000,2)]:
  folder=ROOT/'build/connection-dos'/name;folder.mkdir(parents=True,exist_ok=True)
  for filename in ['HIST.TXT','RVIEW.BIN']:(folder/filename).unlink(missing_ok=True)
  if prefix:(folder/'HIST.TXT').write_bytes(prefix)
  recipe='p3000 c-pgup p300 w h i s t . t x t enter p1200'
  if repeat==2:recipe+=' w h i s t . t x t enter p1200'
  recipe+=' escape p500 r e a d y p500 a-x'
  proof=run(name,'success',recipe,working_drive='d',files={'RVWATCH.COM':observer.read_bytes()},observer='RVWATCH',banner=banner,
   online_updates=[(3.6,b'\x1b[5;1HBACKGROUND\x1b[6n')])
  target=folder/'HIST.TXT';data=target.read_bytes() if target.exists() else b''
  suffix=data[len(prefix):];unit=len(suffix)//repeat
  samples=(folder/'RVIEW.BIN').read_bytes();magic,count,ticks=struct.unpack_from('<3H',samples)
  footers=[samples[6+i*320+240:6+(i+1)*320] for i in range(count)]
  wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()
  proof['checks'].update(history_created=target.exists(),original_prefix_preserved=data.startswith(prefix),
   complete_chronological_lines_exported=lines in suffix,
   same_frozen_snapshot_repeated=unit>0 and suffix==suffix[:unit]*repeat,
   CR_expanded_to_CRLF=b'\r' not in suffix.replace(b'\r\n',b''),
   final_partial_line_preserved=suffix.endswith(b'FIRST BYTE SAFE'),
   later_input_excluded_from_snapshot=b'BACKGROUND' not in suffix,
   observer_saw_success=magic==0x4452 and ticks>0 and any(b'History appended.' in f for f in footers),
   incoming_CPR_while_view_open=b'\x1b[5;11R' in wire,
   live_screen_restored=screen[640:660:2]==b'BACKGROUND',
   export_path_stays_local=b'hist.txt' not in wire.lower(),
   normal_keys_resume=b'ready' in wire)
  proof['export_bytes']=len(suffix);proof['prefix_bytes']=len(prefix);proof['repeat']=repeat
  proof['passed']=all(proof['checks'].values());(folder/'result.json').write_text(json.dumps(proof,indent=2)+'\n')
  cases.append(proof);print(name,'PASS' if proof['passed'] else json.dumps(proof),flush=True)
 folder=ROOT/'build/connection-dos/history-denied';folder.mkdir(parents=True,exist_ok=True)
 assert not (folder/'MISSING').exists()
 proof=run('history-denied','success','p3000 c-pgup p300 w m i s s i n g / p100 b a d . t x t enter p1200 escape p500 r e a d y p500 a-x',working_drive='d',files={'RVWATCH.COM':observer.read_bytes()},observer='RVWATCH',banner=banner)
 samples=(folder/'RVIEW.BIN').read_bytes();count=struct.unpack_from('<H',samples,2)[0]
 footers=[samples[6+i*320+240:6+(i+1)*320] for i in range(count)]
 proof['checks'].update(missing_path_not_created=not (folder/'MISSING').exists(),
  observer_saw_open_denial=any(b'Cannot open history file.' in f for f in footers),
  normal_keys_resume=b'ready' in (folder/'serial.bin').read_bytes())
 proof['passed']=all(proof['checks'].values());(folder/'result.json').write_text(json.dumps(proof,indent=2)+'\n');cases.append(proof)
 sources=['standalone/test_history_export_dos.py','standalone/test_connection_dos.py','standalone/redisplay_watch.asm','src/redisplay/redisplay.c','src/capture/capture_file.c','src/capture/capture_file.h','src/terminal/main.asm']
 report=dict(passed=all(c['passed'] for c in cases),binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=cases,sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},scope='Production DOS main with W filename prompt, exclusive create, real append past70KB, repeated frozen export, independent INT1C footer observer, incoming cursor reply while viewing, prefix/content/CRLF checks and restored hardware/video. No product test mode, original executable or physical disk/modem claim.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed']
if __name__=='__main__':main()
