#!/usr/bin/env python3
"""Build source-only serviced paging controller, decoder and real reserved file owner."""
import argparse,json,re,subprocess
from pathlib import Path
from build_path_session import ROOT,sha,object_segments

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-dCAPTURE_FIXED_RESERVATION']
 units=[('session','src/filesystem/viewer_session.c',True),('decode','src/filesystem/viewer_decode.c',True),
  ('owner','src/filesystem/viewer_file.c',True),('admission','src/filesystem/viewer_admission.c',False),
  ('capture','src/capture/capture_file.c',False),('reservation','src/capture/capture_reservation.c',False),
  ('capturefs','src/capture/capture_fs.c',False),('diagnostic','standalone/viewer_session_diagnostic.c',False)]
 for name,source,bank in units:
  subprocess.run(['wcc',*flags,*(['-nt=FILE_CODE','-nc=FARCODE'] if bank else []),
   '-fo='+str(out/(name+'.obj')),str(ROOT/source)],cwd=out,check=True)
 subprocess.run(['nasm','-fobj',str(ROOT/'src/filesystem/viewer_kernel.asm'),'-o',str(out/'kernel.obj')],check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fm=VIEWPAGE.map','-fe=VIEWPAGE.EXE',
  *[name+'.obj' for name,_,_ in units],'kernel.obj'],cwd=out,check=True)
 segments={n:object_segments(out/(n+'.obj')) for n in ['session','decode','owner']}
 for obj in segments.values():
  assert obj['FILE_CODE']['class']=='FARCODE'
  assert all(not s['bytes'] for n,s in obj.items() if n!='FILE_CODE'),obj
 listing=(out/'VIEWPAGE.map').read_text();group=re.search(r'^DGROUP\s+([0-9a-f]+):',listing,re.M|re.I);assert group
 states={n:re.search(r'^([0-9a-f]+):([0-9a-f]+)[*+ ]+\s+_'+n+r'\s*$',listing,re.M|re.I) for n in ['viewer_file_storage','viewer_session_storage']}
 assert all(s and int(s[1],16)!=int(group[1],16) for s in states.values())
 names=[source for _,source,_ in units]+['src/filesystem/'+n for n in ['viewer_session.h','viewer_decode.h','viewer_file.h','viewer_file_backend.h','viewer_kernel.asm']]+['src/capture/'+n for n in ['capture_file.h','capture_reservation.h','capture_fs.h']]+['standalone/build_viewer_session.py','standalone/build_path_session.py']
 r=dict(binary_sha256=sha(out/'VIEWPAGE.EXE'),sources={n:sha(ROOT/n) for n in names},original_inputs=[],
  component_segments=segments,session_bytes=596,owner_bytes=90,snapshot_bytes=50,persistent_DGROUP_bytes=0,
  scope=__doc__+' Bounded controller component; no viewer UI/terminal dispatch or physical acceptance.')
 (out/'manifest.json').write_text(json.dumps(r,indent=2)+'\n');print('Built VIEWPAGE.EXE',r['binary_sha256'])
if __name__=='__main__':main()
