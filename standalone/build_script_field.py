#!/usr/bin/env python3
"""Source-only parent field staging, actual DOS video and native cursor checks."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--policy',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 units=[('field','src/terminal/script_field.asm',['ASPECT_GET_DISPLAY']),('adapters','src/terminal/script_field_adapters.asm',['ASPECT_GET_DISPLAY','ASPECT_CODE=_TEXT','FARCODE=CODE']),('binding','standalone/script_field_bindings.asm',[])]
 units += [(n,'reconstruction/screen/'+n+'.asm',['SCREEN_OMF']) for n in ('set_cursor','cursor_pack','cursor_output')]
 if a.policy:units=[(name,source,defines+['ASPECT_GET_POLICY']) for name,source,defines in units]
 for name,source,defines in units:
  subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',*['-D'+d for d in defines],str(ROOT/source),'-o',str(out/(name+'.obj'))],check=True)
 # The ordinary parent globs terminal/*.asm. With no opt-in macro, both files
 # must contribute no SEGDEF records (and therefore no code/data segments).
 for name,source,_ in units[:2]:
  obj=out/('disabled-'+name+'.obj');subprocess.run(['nasm','-fobj',str(ROOT/source),'-o',str(obj)],check=True)
  data=obj.read_bytes();at=0
  while at<len(data):
   kind=data[at];length=int.from_bytes(data[at+1:at+3],'little');assert length and at+3+length<=len(data) and kind not in (0x98,0x99)
   at+=3+length
  assert at==len(data)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',*(['-dASPECT_GET_POLICY'] if a.policy else []),'-fd=FIELD.lnk','-fm=FIELD.map','-fe=FIELD.EXE',str(ROOT/'standalone/script_field_driver.c'),*[str(out/(n+'.obj')) for n,_,_ in units]],cwd=out,check=True)
 with (out/'FIELD.lnk').open('a') as f:f.write('\noption packcode=0\n')
 subprocess.run(['wlink','@FIELD.lnk'],cwd=out,check=True)
 symbols={n:int(s,16) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',(out/'FIELD.map').read_text(),re.M|re.I)}
 assert symbols['_field_admit']==symbols['terminal_script_field_admit']==symbols['screen_set_cursor']!=symbols['terminal_script_field']
 assert symbols['terminal_script_window_active']==symbols['terminal_script_confirm_active']==symbols['render_program_owned']==symbols['terminal_script_field_admit']
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nFIELD >CHECK.LOG\nif errorlevel 1 goto failed\necho PASS>RESULT.TXT\nexit\n:failed\necho FAIL>RESULT.TXT\nexit\n')
 with (out/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
 transcript=(out/'CHECK.LOG').read_text().strip();assert (out/'RESULT.TXT').read_text().strip()=='PASS',transcript
 assert transcript.startswith('PASS SCRIPT FIELD 103 cases; ') and transcript.endswith('255 CP437 bytes, persistent video, native cursor, ABI'),transcript
 names=[s for _,s,_ in units]+['standalone/script_field_driver.c','standalone/build_script_field.py','reconstruction/uart/encodings.inc']
 result=dict(parent_policy=a.policy,passed=True,original_inputs=[],disabled_objects_have_no_segments=True,binary_sha256=sha(out/'FIELD.EXE'),cases=103,CP437_bytes=255,transcript=transcript,cpu='8086',sources={n:sha(ROOT/n) for n in names},scope=__doc__+' Opt-in ASPECT_GET_DISPLAY, parent field/adoption adapters with diagnostic segment/class aliases ASPECT_CODE=_TEXT and FARCODE=CODE. Real video/BIOS plus recovered screen_set_cursor/cursor_pack/cursor_output. Parent admission is modeled; no versioned RPC, child/interpreter/serial, whole parent or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(transcript)

if __name__=='__main__':main()
