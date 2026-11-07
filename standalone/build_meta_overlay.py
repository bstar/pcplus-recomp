#!/usr/bin/env python3
"""Source-built matched PCMETA loader and real DOS editor overlay workflow."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
from meta_overlay import split
from check_meta_bank_calls import audit
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--faults',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 bank='meta_editor meta_dialog meta_text meta_file_prompt meta_filename meta_picker meta_picker_scan meta_key_owner meta_key_resource key_editor_file'.split()
 sources=['src/key_mapping/'+n+'.c'for n in bank+['key_actions_dos','meta_loader']]+['src/config/resource_path.c','src/capture/capture_fs.c','src/capture/capture_file.c','src/capture/capture_reservation.c','src/directory/directory_replace.c','src/directory/directory_replace_fs.c','standalone/meta_bank_no_faults.c','standalone/meta_editor_flow_driver.c','standalone/meta_overlay_driver.c']
 if a.faults:sources+=['standalone/meta_loader_faults.c']
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os','-dCAPTURE_FIXED_RESERVATION','-i='+str(ROOT/'src/key_mapping'),'-i='+str(ROOT/'standalone')];objects=[]
 for source in sources:
  name=Path(source).stem;obj=out/(name+'.obj');extra=[]
  if name in bank:
   extra+=['-nt=META_EDITOR_CODE','-nc=FARCODE','-dMETA_EDITOR_BANK']
   extra+=['-d'+n+'=meta_bank_'+n for n in ('memcpy','memset','memcmp','strchr','strcmp','strlen')]
   extra+=['-d_'+n+'=meta_bank_'+n for n in ('fmemcpy','fmemset','fmemcmp','fstrcmp')]
   extra+=['-d'+n+'=meta_bank_'+v for n,v in (('capture_fs_canonical','canonical'),('capture_fs_attributes','attributes'),('directory_replace_paths','paths'),('resource_pcplus_path','resource'),('key_actions_dos_read','actions'))]
  if name=='meta_editor':extra+=['-dmeta_editor_'+n+'=meta_editor_'+n+'_impl'for n in ('open','key','step','draw','cursor','shape','stop','matches','proposal')]
  if name in ('meta_loader','meta_loader_faults'):extra+=['-nt=FILE_CODE','-nc=FARCODE']
  if name=='resource_path':extra+=['-nt=CONFIG_CODE','-nc=FARCODE','-dmemcpy=config_memcpy_service']
  if name=='meta_editor_flow_driver':extra+=['-dmain=meta_bank_flow_main']
  if a.faults and name=='meta_overlay_driver':extra+=['-dMETA_LOADER_FAULTS']
  compile_flags=[f for f in flags if not(name in ('capture_fs','capture_file')and f=='-ecc')]
  subprocess.run(['wcc',*compile_flags,*extra,'-fo='+str(obj),str(ROOT/source)],check=True);objects.append(str(obj))
 asms=['standalone/meta_overlay_host.asm']+['src/key_mapping/'+n+'.asm'for n in ('meta_bank_runtime','meta_bank_entries','meta_bank_kernel','meta_bank_resource','meta_bank_resident','meta_loader_fs','meta_loader_path')]
 for source in asms:
  obj=out/(Path(source).stem+'.obj');subprocess.run(['nasm','-fobj','-I'+str(ROOT/'src/terminal')+'/','-I'+str(ROOT/'src/key_mapping')+'/',*(['-DMETA_LOADER_FAULTS']if a.faults else []),str(ROOT/source),'-o',str(obj)],check=True);objects.append(str(obj))
 subprocess.run(['wcl',*flags,'-k8192','-fd=METAEDIT.lnk','-fm=METAEDIT.map','-fe=METAEDIT.EXE',*objects],cwd=out,check=True)
 response=out/'METAEDIT.lnk';response.write_text(response.read_text()+'\norder clname CODE clname FARCODE clname FARSTATE clname BEGDATA clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@METAEDIT.lnk'],cwd=out,check=True)
 segments={}
 for name in ('meta_loader','meta_loader_fs','meta_loader_path',*(['meta_loader_faults']if a.faults else [])):
  dis=out/(name+'.dis');subprocess.run(['wdis','-l='+str(dis),str(out/(name+'.obj'))],check=True,stdout=subprocess.DEVNULL)
  sizes={n:int(size,16)for n,size in re.findall(r'^Segment: (\S+).*?([0-9A-Fa-f]{8}) bytes$',dis.read_text(),re.M)}
  assert sizes and all(n in ('FILE_CODE','CONFIG_CODE')or not size for n,size in sizes.items()),(name,sizes);segments[name]=sizes
 overlay=split(out/'METAEDIT.EXE',out/'METAEDIT.map','_editor')
 calls=audit(out,[out/(Path(s).stem+'.obj')for s in sources])
 for n in ('LAB','EMPTY','FALL'):(out/n).mkdir()
 (out/'CHECK.BAT').write_text('@echo off\ncd \\LAB\nC:\\METAEDIT >C:\\NORMAL.LOG\nif errorlevel 1 goto bad\necho PASS>C:\\RESULT.TXT\ngoto done\n:bad\necho FAIL>C:\\RESULT.TXT\n:done\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nC:\\CHECK.BAT\nexit\n')
 with(out/'dosbox.log').open('w')as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 logs=(out/'NORMAL.LOG').read_text();assert(out/'RESULT.TXT').read_text().strip()=='PASS',logs
 import struct
 image=re.search(r'IMAGE base (\d+) segment (\d+) bytes (\d+)',logs);assert image
 base,segment,size=map(int,image.groups());expected=bytearray((out/'PCMETA.OVL').read_bytes()[:size])
 for off in struct.unpack_from('<'+'H'*overlay['relocations'],(out/'PCMETA.OVL').read_bytes(),size):struct.pack_into('<H',expected,off,struct.unpack_from('<H',expected,off)[0]+base)
 assert (out/'LOADED.BIN').read_bytes()==expected and segment==base+overlay['relative_target_segment']
 headers=['src/key_mapping/'+n+'.h'for n in bank+['key_actions_dos','meta_loader','key_file_fs','meta_scan_fs']]+['src/config/resource_path.h','src/capture/capture_fs.h','src/capture/capture_file.h','src/capture/capture_reservation.h','src/directory/directory_replace.h','src/directory/directory_replace_fs.h','src/directory/directory_dos.h','standalone/key_editor_faults.h']
 inputs=sources+asms+headers+['src/terminal/far_bridge.inc','src/key_mapping/meta_bank_abi.inc','standalone/meta_overlay.py','standalone/build_meta_overlay.py','standalone/check_meta_bank_calls.py']
 v=dict(passed=True,faults=a.faults,parent_sha256=sha(out/'METAEDIT.EXE'),overlay=overlay,loader_segments=segments,new_loader_DGROUP_bytes=0,exact_relocated_code_sha256=sha(out/'LOADED.BIN'),logs=logs.strip(),call_audit=calls,cpu='8086',sources={n:sha(ROOT/n)for n in inputs},original_inputs=[],scope='Actual extracted, checksum-checked, relocated disk code; full editor workflow, cancel/reload and active lease refusal. Diagnostic retained arena granted by caller. No terminal menu/arena arbitration/live adoption/UART/BBS/physical acceptance.')
 (out/'result.json').write_text(json.dumps(v,indent=2)+'\n');print(logs.strip())
if __name__=='__main__':main()
