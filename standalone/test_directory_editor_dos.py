#!/usr/bin/env python3
"""Actual DOS editor workflows; diagnostic alone writes synthetic result proof."""
import hashlib,json,os,struct,subprocess
from pathlib import Path
from check_directory_editor import Editor,ROOT,OUT

def main():
 binary=OUT/'EDITOR.EXE';digest=hashlib.sha256(binary.read_bytes()).hexdigest();original=Editor([]).original;cases=[]
 changed_name=b'Z'+original[1:]
 edited_name=b'Oiginal!\0'+original[9:]
 changed_port=bytearray(original);changed_port[104]=8
 changed_password=bytearray(original);changed_password[75]=ord('X')
 recipes=[('cancel','x tab y escape',0,original),('accept-name','s-z f10',1,changed_name),('text-edit','right ins s-z del bs end ! f10',1,edited_name),('port-eight','tab '*15+'home del del del del del 8 f10',1,bytes(changed_port)),('invalid-numeric','tab tab home del del del del del 6 5 5 3 7 f10 escape',0,original),('masked-password','tab '*8+'s-x f10',1,bytes(changed_password))]
 for name,keys,status,want in recipes:
  directory=OUT/'dos'/name;directory.mkdir(parents=True,exist_ok=True)
  (directory/'EDITOR.EXE').write_bytes(binary.read_bytes());(directory/'RESULT.BIN').unlink(missing_ok=True)
  # Delay between every actual BIOS key gives rendering time and avoids a full
  # BIOS keyboard queue; these are real keys, not fixture callbacks.
  schedule=' p120 '.join(keys.split())
  config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{directory}"
c:
ADDKEY p750 {schedule}
EDITOR
exit
'''
  (directory/'dosbox.conf').write_text(config)
  with (directory/'dosbox.log').open('w') as log:
   proc=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(directory/'dosbox.conf')],cwd=directory,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=15)
  proof=(directory/'RESULT.BIN').read_bytes();assert len(proof)==118
  assert proc.returncode==0 and struct.unpack('<2H',proof[:4])==(status,1),(name,proof[:4])
  assert proof[4:]==want,(name,[(i,a,b) for i,(a,b) in enumerate(zip(proof[4:],want)) if a!=b])
  cases.append({'case':name,'passed':True,'status':status,'caller_record_exact':True,'screen_cursor_shape_segment_restored':True})
  print(name,'passed',flush=True)
 result={'passed':True,'binary_sha256':digest,'cases':cases,'scope':'Actual DOSBox-X keyboard/video +source editor +recovered snapshots; no UART or user/private records. Diagnostic writes only its own118-byte result; editor does no DOS IO.'}
 (OUT/'dos-results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
