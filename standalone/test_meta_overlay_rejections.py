#!/usr/bin/env python3
"""Actual DOS refusal of damaged/foreign Meta files and ambiguous loader IO."""
import argparse,hashlib,json,os,re,shutil,struct,subprocess,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('direct','fault','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir();builds={n:getattr(a,n).resolve()for n in ('direct','fault')};manifests={}
 for n,build in builds.items():
  assert build.is_relative_to(ROOT/'build');v=json.loads((build/'result.json').read_text());assert v['passed']and v['faults']==(n=='fault') and sha(build/'METAEDIT.EXE')==v['parent_sha256']and sha(build/'PCMETA.OVL')==v['overlay']['sha256'];manifests[n]=v
  for s,h in v['sources'].items():assert sha(ROOT/s)==h,s
 base=builds['direct'];m=manifests['direct'];payload=(base/'PCMETA.OVL').read_bytes();exe=(base/'METAEDIT.EXE').read_bytes();h=struct.unpack_from('<14H',exe);listing=(base/'METAEDIT.map').read_text();point=re.search(r'^([0-9a-f]+):([0-9a-f]+)[*+]?\s+_meta_loader_expected$',listing,re.M|re.I);assert point
 at=h[4]*16+int(point[1],16)*16+int(point[2],16);size=m['overlay']['bank_bytes'];count=m['overlay']['relocations'];assert count>=2
 def crc_parent(data):
  parent=bytearray(exe);struct.pack_into('<I',parent,at+8,zlib.crc32(data));return bytes(parent)
 cases=[('missing',3,None,exe,'direct',None),('short',3,payload[:-1],exe,'direct',None),('trailing',3,payload+b'X',exe,'direct',None)]
 bad=bytearray(payload);bad[0]^=1;cases.append(('checksum',4,bytes(bad),exe,'direct',None))
 foreign=(builds['fault']/'PCMETA.OVL').read_bytes();assert foreign!=payload;cases.append(('foreign-parent',4,foreign,exe,'direct',None))
 for name,first,second in [('fixup-outside',size-1,None),('fixup-duplicate',None,'duplicate'),('fixup-overlap',None,'overlap'),('fixup-order',None,'order')]:
  data=bytearray(payload);points=list(struct.unpack_from('<'+'H'*count,data,size))
  if first is not None:points[0]=first
  if second=='duplicate':points[1]=points[0]
  if second=='overlap':points[1]=points[0]+1
  if second=='order':points[0],points[1]=points[1],points[0]
  struct.pack_into('<'+'H'*count,data,size,*points);cases.append((name,5,bytes(data),crc_parent(data),'direct',None))
 data=bytearray(payload);first=struct.unpack_from('<H',data,size)[0];struct.pack_into('<H',data,first,0xffff);cases.append(('fixup-segment',5,bytes(data),crc_parent(data),'direct',None))
 for name,off,value in [('header-version',2,2),('header-small',4,255),('header-large',4,24001),('header-fixup-limit',6,513),('header-data',14,0xffff),('header-arena',18,0)]:
  parent=bytearray(exe);struct.pack_into('<H',parent,at+off,value);cases.append((name,1,payload,bytes(parent),'direct',None))
 for name,reason,mode in [('read-error',3,1),('short-read',3,2),('close-after',6,3),('close-before',6,4)]:cases.append((name,reason,(builds['fault']/'PCMETA.OVL').read_bytes(),(builds['fault']/'METAEDIT.EXE').read_bytes(),'fault',mode))
 rows=[]
 for name,reason,data,parent,kind,mode in cases:
  folder=out/name;folder.mkdir();(folder/'LAB').mkdir();(folder/'METAEDIT.EXE').write_bytes(parent)
  if data is not None:(folder/'PCMETA.OVL').write_bytes(data)
  (folder/'CHECK.BAT').write_text('@echo off\nset PCPLUS=C:\\MISSING\ncd \\LAB\nC:\\METAEDIT '+str(reason)+(' '+str(mode)if mode else'')+' >C:\\REPORT.TXT\nif errorlevel 1 goto bad\necho PASS>C:\\RESULT.TXT\ngoto done\n:bad\necho FAIL>C:\\RESULT.TXT\n:done\nexit\n')
  (folder/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{folder}"\nc:\nC:\\CHECK.BAT\nexit\n')
  with(folder/'dosbox.log').open('w')as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=20)
  text=(folder/'REPORT.TXT').read_text().strip();assert(folder/'RESULT.TXT').read_text().strip()=='PASS'and text.startswith('PASS loader'),(name,text)
  assert not(folder/'LOADED.BIN').exists()and not list((folder/'LAB').iterdir()),name
  rows.append(dict(case=name,reason=reason,fault_mode=mode,report=text,parent_sha256=sha(folder/'METAEDIT.EXE'),payload_sha256=sha(folder/'PCMETA.OVL')if data is not None else None));print(name,'PASS',flush=True)
 result=dict(passed=True,cases=rows,original_inputs=[],producers={n:dict(parent_sha256=v['parent_sha256'],overlay_sha256=v['overlay']['sha256'])for n,v in manifests.items()},sources={'standalone/test_meta_overlay_rejections.py':sha(Path(__file__))},scope=__doc__+' Metadata-only mutations of source-built parents allow testing bad fixup tables against matched CRCs; no damaged module code executes. HELD close faults forbid retry/unload/reset until DOS exit. No physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(rows),'actual DOS Meta loader refusal cases')
if __name__=='__main__':main()
