#!/usr/bin/env python3
"""Actual DOSBox-X browser key paths against synthetic read-only directory data."""
import hashlib,json,os,struct,subprocess
from pathlib import Path
from check_directory_browser import fixture,ROOT,OUT

def main():
 binary=OUT/'BROWSER.EXE';digest=hashlib.sha256(binary.read_bytes()).hexdigest();cases=[]
 recipes=[('navigation','end p150 pgup p150 home p150 down p150 pgdown p150 up p150 enter',0,11,False,False),('cancel','down p150 escape',1,0,False,False),('last-entry','end p150 down p150 pgdown p150 enter',0,200,False,False),('legacy','down p150 enter',0,2,True,False),('file-error','',2,0,False,True)]
 for name,keys,status,entry,legacy,missing in recipes:
  directory=OUT/'dos'/name;directory.mkdir(parents=True,exist_ok=True)
  (directory/'BROWSER.EXE').write_bytes(binary.read_bytes());(directory/'RESULT.BIN').unlink(missing_ok=True)
  data=fixture()
  if missing:(directory/'NORMAL.DIR').unlink(missing_ok=True)
  else:(directory/'NORMAL.DIR').write_bytes(data)
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
'''
  if keys:config+='ADDKEY p750 '+keys+'\n'
  config+='BROWSER'+(' L' if legacy else '')+'\nexit\n'
  (directory/'dosbox.conf').write_text(config)
  with (directory/'dosbox.log').open('w') as log:
   proc=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(directory/'dosbox.conf')],cwd=directory,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=15)
  proof=struct.unpack('<5H',(directory/'RESULT.BIN').read_bytes())
  assert proc.returncode==0 and proof==(status,entry,0x0711,1,int(legacy)),(name,proof)
  assert missing or (directory/'NORMAL.DIR').read_bytes()==data
  cases.append({'case':name,'passed':True,'status':status,'entry':entry,'BIOS_cursor':proof[2],'screen_shape_and_video_segment_restored':True,'legacy':legacy,'directory_unchanged':not missing})
  print(name,'passed',flush=True)
 result={'passed':True,'binary_sha256':digest,'cases':cases,'scope':'Actual DOSBox-X BIOS keyboard/video, complete compiled DOS directory reader and recovered snapshots. Synthetic directory only; no UART or original/private data.'}
 (OUT/'dos-results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
