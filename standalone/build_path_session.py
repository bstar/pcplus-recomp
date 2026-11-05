#!/usr/bin/env python3
"""Build source-only FILE_CODE path-session lifecycle diagnostic."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def object_segments(path):
 data=path.read_bytes();pos=0;names=[''];result={}
 def index(d,j):
  value=d[j]
  return (((value&127)<<8)|d[j+1],j+2) if value&128 else (value,j+1)
 while pos<len(data):
  tag=data[pos];size=int.from_bytes(data[pos+1:pos+3],'little');d=data[pos+3:pos+2+size];pos+=size+3
  if tag==0x96:
   j=0
   while j<len(d):n=d[j];j+=1;names.append(d[j:j+n].decode());j+=n
  if tag==0x98:
   j=1 if d[0]&0xe0 else 4
   size=int.from_bytes(d[j:j+2],'little');j+=2;name,j=index(d,j);cls,j=index(d,j)
   result[names[name]]={'class':names[cls],'bytes':size}
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 native=ROOT/'reconstruction/file_path/change.asm';proof=json.loads(native.with_name('provenance.json').read_text())
 subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(native),'-o',str(out/'change.bin')],check=True)
 assert sha(out/'change.bin')==proof['sha256']
 bank=['-D_TEXT=FILE_CODE','-DCODE=FARCODE']
 subprocess.run(['nasm','-fobj','-DFILE_PATH_OMF',*bank,'-I'+str(ROOT/'reconstruction/uart')+'/',str(native),'-o',str(out/'change.obj')],check=True)
 aliases=['path_native_change=path_native_real','path_current_drive=path_drive_real','path_select_drive=path_select_real','path_getcwd=path_cwd_real']
 subprocess.run(['nasm','-fobj',*bank,*['-D_'+n.replace('=','=_') for n in aliases],str(ROOT/'src/filesystem/path_kernel.asm'),'-o',str(out/'kernel.obj')],check=True)
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we']
 units=[('session','src/filesystem/path_session.c',True,[]),('owner','src/filesystem/path_owner.c',True,[]),
        ('boundary','standalone/path_session_diagnostic.c',True,['-dPATH_SESSION_BOUNDARY']),('diagnostic','standalone/path_session_diagnostic.c',False,[])]
 for name,source,banked,extra in units:
  subprocess.run(['wcc',*flags,*(['-nt=FILE_CODE','-nc=FARCODE'] if banked else []),*extra,'-fo='+str(out/(name+'.obj')),str(ROOT/source)],cwd=out,check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fm=SESSION.map','-fe=SESSION.EXE',*[n+'.obj' for n,_,_,_ in units],'change.obj','kernel.obj'],cwd=out,check=True)
 listing=(out/'SESSION.map').read_text()
 segments={n:(int(s,16),int(o,16),int(size,16)) for n,s,o,size in re.findall(r'^(\w+)\s+\w+\s+\S+\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I)}
 syms={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 group=re.search(r'^DGROUP\s+([0-9a-f]+):([0-9a-f]+)',listing,re.M|re.I);assert group
 state=syms['_path_session_storage'];filecode=segments['FILE_CODE'];data=int(group[1],16)
 assert state[0]==filecode[0] and state[0]!=data and state[1]+76<=filecode[1]+filecode[2],(state,filecode,data)
 session_segments=object_segments(out/'session.obj')
 assert session_segments['FILE_CODE']['class']=='FARCODE'
 assert all(not segment['bytes'] for name,segment in session_segments.items() if name!='FILE_CODE'),session_segments
 names=['src/filesystem/path_session.c','src/filesystem/path_session.h','src/filesystem/path_owner.c','src/filesystem/path_owner.h','src/filesystem/path_kernel.asm','reconstruction/file_path/change.asm','reconstruction/file_path/provenance.json','reconstruction/uart/encodings.inc','standalone/path_session_diagnostic.c','standalone/build_path_session.py']
 result=dict(kind='source-only-FILE_CODE-path-session-diagnostic',binary_sha256=sha(out/'SESSION.EXE'),sources={n:sha(ROOT/n) for n in names},original_inputs=[],state_bytes=76,state_segment=state[0],state_offset=state[1],DGROUP_segment=data,FILE_CODE=segments['FILE_CODE'],session_object_segments=session_segments,limitations=['Standalone synchronous owner; no application/menu/UART admission.','Explicit kernel fault wrappers are not physical DOS failures.'])
 (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built SESSION.EXE',result['binary_sha256'],'state',state,'DGROUP',data)
if __name__=='__main__':main()
