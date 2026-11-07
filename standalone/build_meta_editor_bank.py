#!/usr/bin/env python3
"""Separate-CS Meta bank ABI, actual DOS kernel, DTA and ownership workflow."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
from check_meta_bank_calls import audit
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-services',action='store_true',help='Production callbacks and in-bank far memory services; mixed register/cdecl host.');p.add_argument('--direct',action='store_true',help='Execute the unwrapped production kernel; no injected-failure run.');p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 bank_units=('meta_editor','meta_dialog','meta_text','meta_file_prompt','meta_filename','meta_picker','meta_picker_scan','meta_key_owner','meta_key_resource','key_editor_file')
 units=bank_units+('key_actions_dos',)
 sources=['src/key_mapping/'+n+'.c' for n in units]+['src/config/resource_path.c','src/capture/capture_fs.c','src/capture/capture_file.c','src/capture/capture_reservation.c','src/directory/directory_replace.c','src/directory/directory_replace_fs.c','standalone/'+('meta_bank_no_faults.c' if a.direct else 'key_editor_faults.c'),'standalone/meta_editor_flow_driver.c','standalone/meta_bank_driver.c','standalone/meta_bank_kernel_probe.c']
 if a.parent_services:sources+=['standalone/meta_bank_memory_probe.c','standalone/meta_bank_memory_reference.c']
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os','-dCAPTURE_FIXED_RESERVATION','-i='+str(ROOT/'src/key_mapping'),'-i='+str(ROOT/'standalone')];objects=[]
 for source in sources:
  obj=out/(Path(source).stem+'.obj');extra=[]
  if source.endswith('key_actions_dos.c') and not a.parent_services:extra=['-dKEY_RESOURCE_PRIVATE_READS']
  if Path(source).stem in bank_units or Path(source).stem in ('key_editor_faults','meta_bank_no_faults','meta_bank_kernel_probe','meta_bank_memory_probe'):
   extra+=['-nt=META_EDITOR_CODE','-nc=FARCODE','-dMETA_EDITOR_BANK']
   extra+=['-d'+n+'=meta_bank_'+n for n in ('memcpy','memset','memcmp','strchr','strcmp','strlen')]
   extra+=['-d_'+n+'=meta_bank_'+n for n in ('fmemcpy','fmemset','fmemcmp','fstrcmp')]
   extra+=['-d'+n+'=meta_bank_'+alias for n,alias in (('capture_fs_canonical','canonical'),('capture_fs_attributes','attributes'),('directory_replace_paths','paths'),('resource_pcplus_path','resource'),('key_actions_dos_read','actions'))]
  if Path(source).stem=='meta_editor':extra+=['-dmeta_editor_'+n+'=meta_editor_'+n+'_impl' for n in ('open','key','step','draw','cursor','shape','stop','matches','proposal')]
  if Path(source).stem in ('key_editor_faults','meta_bank_no_faults'):extra+=['-dkey_fault_reset=key_fault_reset_impl','-dstrstr=meta_bank_strstr']
  if source.endswith('meta_bank_kernel_probe.c') and not a.direct:extra+=['-dMETA_BANK_TEST_FAULTS']
  if a.parent_services and source.endswith('meta_bank_driver.c'):extra+=['-dMETA_PARENT_SERVICES']
  if source.endswith('meta_editor_flow_driver.c'):extra+=['-dmain=meta_bank_flow_main']
  if a.parent_services and source.endswith('resource_path.c'):extra+=['-nt=CONFIG_CODE','-nc=FARCODE','-dmemcpy=config_memcpy_service']
  compile_flags=[f for f in flags if not (a.parent_services and Path(source).name in ('capture_fs.c','capture_file.c') and f=='-ecc')]
  subprocess.run(['wcc',*compile_flags,*extra,'-fo='+str(obj),str(ROOT/source)],check=True);objects.append(str(obj))
 segments={}
 for unit in bank_units:
  dis=out/(unit+'.dis');subprocess.run(['wdis','-l='+str(dis),str(out/(unit+'.obj'))],check=True,stdout=subprocess.DEVNULL)
  sizes={n:int(size,16) for n,size in re.findall(r'^Segment: (\S+).*?([0-9A-Fa-f]{8}) bytes$',dis.read_text(),re.M)}
  assert sizes and all(n=='META_EDITOR_CODE' or not size for n,size in sizes.items()),(unit,sizes)
  segments[unit]=sizes
 asms=['standalone/meta_editor_banks.asm','standalone/'+('meta_bank_parent_host.asm' if a.parent_services else 'meta_bank_host.asm'),'src/key_mapping/'+('meta_bank_runtime.asm' if a.parent_services else 'meta_bank_crt.asm'),'src/key_mapping/meta_bank_entries.asm','src/key_mapping/meta_bank_kernel.asm']
 if a.parent_services:asms+=['src/key_mapping/meta_bank_resource.asm','src/key_mapping/meta_bank_resident.asm']
 for asm in asms:
  obj=out/(Path(asm).stem+'.obj');subprocess.run(['nasm','-fobj','-I'+str(ROOT/'src/terminal')+'/', '-I'+str(ROOT/'src/key_mapping')+'/', *(['-DMETA_BANK_TEST_FAULTS'] if not a.direct else []),str(ROOT/asm),'-o',str(obj)],check=True);objects.append(str(obj))
 subprocess.run(['wcl',*flags,'-k8192','-fd=METAEDIT.lnk','-fm=METAEDIT.map','-fe=METAEDIT.EXE',*objects],cwd=out,check=True)
 response=out/'METAEDIT.lnk';response.write_text(response.read_text()+'\norder clname CODE clname FARPAD clname FARCODE clname FARSTATE clname BEGDATA clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@METAEDIT.lnk'],cwd=out,check=True)
 payload=sum(v['META_EDITOR_CODE'] for v in segments.values());product_asm={}
 for name in (('meta_bank_runtime' if a.parent_services else 'meta_bank_crt'),'meta_bank_entries','meta_bank_kernel'):
  dis=out/(name+'.dis');subprocess.run(['wdis','-l='+str(dis),str(out/(name+'.obj'))],check=True,stdout=subprocess.DEVNULL)
  sizes={n:int(size,16) for n,size in re.findall(r'^Segment: (\S+).*?([0-9A-Fa-f]{8}) bytes$',dis.read_text(),re.M)}
  assert sizes and all(n=='META_EDITOR_CODE' or not size for n,size in sizes.items()),(name,sizes)
  product_asm[name]=sizes;payload=(payload+15)//16*16+sizes['META_EDITOR_CODE']
 service_segments={}
 if a.parent_services:
  for name,segment,expected in (('meta_bank_resident','_TEXT',44),('meta_bank_resource','CONFIG_CODE',20)):
   dis=out/(name+'.dis');subprocess.run(['wdis','-l='+str(dis),str(out/(name+'.obj'))],check=True,stdout=subprocess.DEVNULL)
   sizes={n:int(size,16) for n,size in re.findall(r'^Segment: (\S+).*?([0-9A-Fa-f]{8}) bytes$',dis.read_text(),re.M)}
   assert sizes=={segment:expected},(name,sizes);service_segments[name]=sizes
 assert 12870<=16384 and 16384+payload<=61000
 listing=(out/'METAEDIT.map').read_text();data=re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);null=re.search(r'^_NULL\s+BEGDATA\s+DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);assert data and null and data[1]==null[1]
 code=re.search(r'^META_EDITOR_CODE\s+FARCODE\s+[^\n]*?([0-9a-f]+):0000\s+([0-9a-f]+)',listing,re.M|re.I)
 main=re.search(r'^_TEXT\s+CODE\s+[^\n]*?([0-9a-f]+):0000',listing,re.M|re.I)
 assert code and main,(code,main)
 assert (int(code[1],16)-int(main[1],16))*16>=65536
 assert payload<=24000
 assert int(code[2],16)<=(30000 if a.parent_services else 24000),code[0]
 assert 16384+int(code[2],16)<=63000

 calls=audit(out,[out/(Path(s).stem+'.obj') for s in sources])
 for n in ('LAB','EMPTY','FALL'):(out/n).mkdir()
 (out/'CHECK.BAT').write_text('@echo off\ncd \\LAB\nC:\\METAEDIT >C:\\NORMAL.LOG\nif errorlevel 1 goto failed'+('' if a.direct else '\nC:\\METAEDIT 1 >C:\\FATAL.LOG\nif errorlevel 1 goto failed')+'\necho PASS>C:\\RESULT.TXT\ngoto done\n:failed\necho FAIL>C:\\RESULT.TXT\n:done\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nC:\\CHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=60)
 logs={n:(out/n).read_text().strip() for n in ('NORMAL.LOG','FATAL.LOG') if (out/n).exists()};assert (out/'RESULT.TXT').read_text().strip()=='PASS',logs
 headers=['src/key_mapping/'+n+'.h' for n in units]+['src/key_mapping/key_file_fs.h','src/key_mapping/meta_scan_fs.h','src/config/resource_path.h','src/capture/capture_fs.h','src/capture/capture_file.h','src/capture/capture_reservation.h','src/directory/directory_replace.h','src/directory/directory_replace_fs.h','src/directory/directory_dos.h','standalone/key_editor_faults.h']
 inputs=sources+headers+asms+['src/terminal/far_bridge.inc','src/key_mapping/meta_bank_abi.inc','standalone/build_meta_editor_bank.py','standalone/check_meta_bank_calls.py'];result=dict(passed=True,direct_kernel=a.direct,parent_services=a.parent_services,call_audit=calls,binary_sha256=sha(out/'METAEDIT.EXE'),logs=logs,cpu='8086',original_inputs=[],bank_segments=segments,bank_bytes=int(code[2],16),product_assembly_segments=product_asm,new_parent_service_segments=service_segments,calculated_product_payload_bytes=payload,planned_state_offset=0,planned_payload_offset=16384,arena_bytes=63000,snapshot_image_offset=61000,bank_paragraph=int(code[1],16),resident_paragraph=int(main[1],16),entry_state_bytes=12870,editor_owned_DGROUP_bytes=0,sources={s:sha(ROOT/s) for s in inputs},scope='Separate-CS bank (forced 64KiB gap), direct DOS kernel and parent callback adapters; composed editor model/frames, real DOS KEY lookup/enumeration/claims/checked IO and failure quarantine. Explicit admission flag is supplied by test caller; output is an unadopted proposal. No transient loading/unloading, production callback placement, terminal adoption, actual VGA/UART/parent capacity/BBS/hardware acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(logs)
if __name__=='__main__':main()
