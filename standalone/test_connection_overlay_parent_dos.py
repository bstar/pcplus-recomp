#!/usr/bin/env python3
"""Run the actual full-parent PCCONN (shared owner kind5) startup loader in DOS.

The parent comes from build_terminal.py --connection-arena-probe. Before UART
startup it loads the packaged module through the unchanged shared loader,
checks exclusion with the compiler owner, dumps the allocated image, releases,
overwrites the extent, reloads and dumps it again. The module is never
entered. No child RPC, serial session, DIAL execution or hardware claim.
"""
import argparse,hashlib,json,os,re,shutil,struct,subprocess,sys,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from directory_fixtures import prm
import connection_module as cm
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CASES=['valid','missing','corrupt','truncated','fixup-range','fixup-order','descriptor-extent']
NOTICE=b'\r\nUnsupported keyboard binding or local command; terminal stopped.\r\n'


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','module','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--case',choices=CASES,default='valid')
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['binary_sha256']==sha(binary)
 info=m['diagnostic_connection_arena_probe'];raw_module=a.module.read_bytes()
 assert cm.sha(raw_module)==info['source_mz_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir()
 for leaf in ('TERMINAL.EXE','PCLINE.OVL','PCMETA.OVL','PCCOMP.OVL','PCCONN.OVL'):shutil.copyfile(binary.with_name(leaf),out/leaf)
 data=bytearray((out/'PCCONN.OVL').read_bytes());assert cm.sha(data)==info['sha256']
 parent=bytearray((out/'TERMINAL.EXE').read_bytes())
 anchor=re.search(r'^([0-9a-f]+):([0-9a-f]+)[*+ ]*\s+_connection_overlay_expected\b',binary.with_name('terminal.map').read_text(),re.M|re.I)
 at=struct.unpack_from('<14H',parent)[4]*16+int(anchor[1],16)*16+int(anchor[2],16)
 descriptor=struct.unpack_from('<11H',parent,at);assert descriptor[:2]==(0x4e43,1)
 n,size=info['relocations'],info['payload_bytes']
 if a.case=='missing':(out/'PCCONN.OVL').unlink()
 elif a.case=='descriptor-extent':struct.pack_into('<H',parent,at+18,16386)
 elif a.case!='valid':
  if a.case=='corrupt':data[0]^=1
  elif a.case=='truncated':data.pop()
  else:
   if a.case=='fixup-range':struct.pack_into('<H',data,size+2*(n-1),size)
   else:struct.pack_into('<H',data,size+2*(n-1),struct.unpack_from('<H',data,size+2*(n-2))[0])
   # CRC still matches, so the loader's fixup-rule refusal is what is tested.
   struct.pack_into('<I',parent,at+8,zlib.crc32(data))
  (out/'PCCONN.OVL').write_bytes(data)
 (out/'TERMINAL.EXE').write_bytes(parent)
 (out/'TEST.PRM').write_bytes(prm(port=3,baud=5))
 (out/'CHECK.BAT').write_bytes(b'@echo off\r\nset PCPLUS=C:\\MISSING\r\nC:\\TERMINAL @C:\\TEST.PRM >C:\\REPORT.BIN\r\nif errorlevel 1 goto bad\r\necho PASS>C:\\RESULT.TXT\r\ngoto done\r\n:bad\r\necho FAIL>C:\\RESULT.TXT\r\n:done\r\nexit\r\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nC:\\CHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
 got=(out/'REPORT.BIN').read_bytes();result=(out/'RESULT.TXT').read_text().strip()
 image=info['allocated_image_bytes'];checks={}
 if a.case=='valid':
  assert len(got)==32+2*image,(len(got),got[-80:])
  first=struct.unpack('<8H',got[:16]);final=struct.unpack('<8H',got[-16:])
  assert first[:4]==(0x5043,1,7,0) and final[:5]==(0x5043,1,14,0,0) and result=='PASS',(first,final)
  segment,psp=first[5],first[7]
  assert first[5:]==final[5:] and first[6]==image and segment==psp+16+info['target_segment'],(first,final)
  # Exactly a DOS MZ load at the arena, with BSS/stack zeroed to the image end.
  expected=cm.mz_load(raw_module,segment)+bytes(image-size)
  dumps=got[16:16+image],got[16+image:16+2*image]
  for i,dump in enumerate(dumps):assert dump==expected,(i,next(j for j in range(image) if dump[j]!=expected[j]))
  checks=dict(load_reload_images_match_mz=2,arena_segment=f'{segment:04x}',psp=f'{psp:04x}',zeroed_bss_bytes=image-size,
   exclusion=['duplicate_connection_load','compiler_load','compiler_release','compiler_phase_ffff'],
   reload_over_a5_fill=True,report=list(final))
 else:
  assert got.endswith(NOTICE) and len(got)==16+len(NOTICE) and result=='FAIL',got
  final=struct.unpack('<8H',got[:16])
  phase=0xffff if a.case=='descriptor-extent' else 0
  assert final[:6]==(0x5043,1,1,4,phase,0) and final[6]==0,final
  checks=dict(load_refused=4,final_phase=phase,report=list(final))
 for name,h in m['sources'].items():assert sha(ROOT/name)==h,name
 d=dict(passed=True,case=a.case,parent_sha256=sha(binary),tested_parent_sha256=sha(out/'TERMINAL.EXE'),module_sha256=info['sha256'],
  source_mz_sha256=info['source_mz_sha256'],checks=checks,original_inputs=[],production_integrated=False,physical_verified=False,
  sources={n:sha(ROOT/n) for n in ['standalone/test_connection_overlay_parent_dos.py','standalone/connection_module.py','standalone/directory_fixtures.py']},
  scope=__doc__.strip()+' DOSBox-X 8086/FPU-off actual DOS. Fault fixtures change only the copied module or owned diagnostic parent.')
 (out/'result.json').write_text(json.dumps(d,indent=2)+'\n')
 for leaf in ('TERMINAL.EXE','PCLINE.OVL','PCMETA.OVL','PCCOMP.OVL','PCCONN.OVL','REPORT.BIN'):
  if (out/leaf).exists():(out/leaf).unlink() # Keep build/ small; hashes are recorded.
 print('PASS connection parent startup:',a.case,checks.get('report'))


if __name__=='__main__':main()
