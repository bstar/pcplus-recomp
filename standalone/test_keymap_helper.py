#!/usr/bin/env python3
"""Actual foreground DOS helper workflows on owned synthetic KBD media."""
import argparse,ast,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def image():
 return b''.join((f'P{p:02}{s:02}'.encode()+b'\0'+bytes([0xa5,p+1,s+1,0xff,0xae,0x5a])) for p in range(33) for s in range(79))
def changed(raw,p=6,s=16):
 out=bytearray(raw);at=p*948+s*12;out[at:at+4]=b'new\0';return bytes(out)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();build=a.build.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 manifest=json.loads((build/'result.json').read_text());assert manifest['passed'] and not manifest['original_inputs'] and sha(build/'PCKEYMAP.EXE')==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 tree=ast.parse((ROOT/'standalone/test_meta_dialog_vga.py').read_text());sampler=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='sampler' for t in n.targets))
 edit='f1 p60 tab n e w enter p120 '
 cases=[('ready',6,'escape',None),('cancel',6,'f1 p60 tab n e w escape p120 escape',None),('save',6,edit+'a-s p350 escape',6),('discard',6,edit+'escape p100 n',None),('save-on-exit',6,edit+'escape p100 y',6),('cancel-exit',6,edit+'escape p100 escape p120 a-s p350 escape',6),('next-wrap',32,'space p100 '+edit+'a-s p350 escape',0),('previous-wrap',0,'pgup p100 '+edit+'a-s p350 escape',32),('open-missing-discard',6,edit+'a-o p100 n p100 m i s s i n g enter p250 space p120 escape',None),('open',6,'a-o p100 n e x t enter p250 '+edit+'a-s p350 escape',6),('legacy',6,edit+'a-s p350 escape',6),('long',6,'f1 p120 space p120 escape',None),('conflict',6,edit+'a-s p150 space p120 escape p100 n',None),('readonly',6,edit+'a-s p150 space p120 escape p100 n',None)]
 results=[];base=image();assert len(base)==31284
 for name,profile,keys,edited_profile in cases:
  case=out/name;case.mkdir();shutil.copyfile(build/'PCKEYMAP.EXE',case/'PCKEYMAP.EXE');initial=base
  if name=='ready':initial=bytes(31284)
  if name=='long':buf=bytearray(base);buf[6*948+16*12:6*948+17*12]=b'\x1e'*11+b'\0';initial=bytes(buf)
  (case/'SYN.KBD').write_bytes(initial);(case/'NEXT.KBD').write_bytes(base)
  if name=='conflict':(case/'KBDSTG.$$$').write_bytes(b'OWNED CONFLICT')
  for leaf in ('BEFORE','AFTER'):
   source=case/(leaf+'.ASM');source.write_text(sampler.replace('BEFORE.BIN',leaf+'.BIN'));subprocess.run(['nasm','-fbin',str(source),'-o',str(case/(leaf+'.COM'))],check=True)
  if name=='ready':
   watch=(ROOT/'standalone/path_dialog_watch.asm').read_text();start=watch.index(' cmp word [es:806]');end=watch.index('%if WATCH_KIND',start)
   marker=" xor di,di\n.find:\n mov bx,di\n mov si,title\n mov cx,17\n.match:\n mov al,[si]\n cmp al,[es:bx]\n jne .next\n inc si\n add bx,2\n loop .match\n jmp .found\n.next:\n add di,2\n cmp di,3966\n jbe .find\n jmp .done\n.found:\n"
   watch=(watch[:start]+marker+watch[end:]).replace('last_sum: dw 0',"title: db 'PgUp/Dn:Terminals'\nlast_sum: dw 0").replace('D:\\PATHVIEW.BIN','C:\\PATHVIEW.BIN')
   (case/'WATCH.ASM').write_text(watch);subprocess.run(['nasm','-fbin','-DWATCH_KIND=0',str(case/'WATCH.ASM'),'-o',str(case/'WATCH.COM')],check=True)
  (case/'CHECK.BAT').write_text('@echo off\ncls\n'+('attrib +r SYN.KBD\n' if name=='readonly' else '')+'BEFORE\n'+('WATCH T\n' if name=='ready' else '')+'ADDKEY p700 '+keys+'\nPCKEYMAP '+str(profile)+' SYN.KBD'+(' /LEGACY' if name in ('legacy','previous-wrap') else '')+'\nif errorlevel 1 goto failed\nAFTER\n'+('WATCH\n' if name=='ready' else '')+'echo PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
  (case/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "'+str(case)+'"\nc:\nCHECK.BAT\nexit\n')
  with (case/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(case/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=20)
  assert (case/'PASS.TXT').exists() and not (case/'FAIL.TXT').exists(),name
  assert (case/'BEFORE.BIN').read_bytes()==(case/'AFTER.BIN').read_bytes(),(name,'screen/shape/cursor')
  expected=changed(initial,edited_profile) if edited_profile is not None and name!='open' else initial
  assert (case/'SYN.KBD').read_bytes()==expected,(name,'SYN')
  assert (case/'NEXT.KBD').read_bytes()==(changed(base) if name=='open' else base),(name,'NEXT')
  assert not (case/'MISSING.KBD').exists()
  assert not (case/'KBDBAK.$$$').exists()
  if name=='conflict':assert (case/'KBDSTG.$$$').read_bytes()==b'OWNED CONFLICT'
  else:assert not (case/'KBDSTG.$$$').exists()
  if name=='ready':
   raw=(case/'PATHVIEW.BIN').read_bytes();assert raw[:4]==b'\x44\x50\x03\x00'
   reference=json.loads((ROOT/'docs/validation/keymap-screen.json').read_text());assert hashlib.sha256(raw[6:4006]).hexdigest()==reference['frame_sha256']
  results.append(dict(name=name,passed=True,exact_files=True,screen_cursor_shape_restored=True));print('PASS',name,flush=True)
 result=dict(passed=True,binary_sha256=manifest['binary_sha256'],cases=results,original_inputs=[],cpu='8086',private_data_inputs=False,sources={n:sha(ROOT/n) for n in ['standalone/test_keymap_helper.py','standalone/test_meta_dialog_vga.py','standalone/path_dialog_watch.asm','docs/validation/keymap-screen.json']},scope='Actual standalone foreground helper edit/cancel/save/open/profile wrap/refusals/restore on synthetic files. No parent EXEC, factory defaults, physical or modem acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
