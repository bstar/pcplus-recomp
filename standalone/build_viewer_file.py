#!/usr/bin/env python3
"""Build source-only banked read-only viewer owner with actual capture reservation."""
import argparse,json,re,subprocess
from pathlib import Path
from build_path_session import ROOT,sha,object_segments

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-dCAPTURE_FIXED_RESERVATION']
 units=[('owner','src/filesystem/viewer_file.c',True),('admission','src/filesystem/viewer_admission.c',False),
  ('capture','src/capture/capture_file.c',False),('reservation','src/capture/capture_reservation.c',False),
  ('capturefs','src/capture/capture_fs.c',False),('diagnostic','standalone/viewer_file_diagnostic.c',False)]
 for name,source,bank in units:
  subprocess.run(['wcc',*flags,*(['-nt=FILE_CODE','-nc=FARCODE'] if bank else []),
   '-fo='+str(out/(name+'.obj')),str(ROOT/source)],cwd=out,check=True)
 subprocess.run(['nasm','-fobj',str(ROOT/'src/filesystem/viewer_kernel.asm'),'-o',str(out/'kernel.obj')],check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fm=VIEWFILE.map','-fe=VIEWFILE.EXE',
  *[name+'.obj' for name,_,_ in units],'kernel.obj'],cwd=out,check=True)
 segments=object_segments(out/'owner.obj');assert segments['FILE_CODE']['class']=='FARCODE'
 assert all(not s['bytes'] for n,s in segments.items() if n!='FILE_CODE'),segments
 listing=(out/'VIEWFILE.map').read_text();state=re.search(r'^([0-9a-f]+):([0-9a-f]+)[*+ ]+\s+_viewer_file_storage\s*$',listing,re.M|re.I);group=re.search(r'^DGROUP\s+([0-9a-f]+):',listing,re.M|re.I)
 assert state and group and int(state[1],16)!=int(group[1],16)
 names=[source for _,source,_ in units]+['src/filesystem/viewer_file.h','src/filesystem/viewer_file_backend.h',
  'src/filesystem/viewer_kernel.asm','src/capture/capture_file.h','src/capture/capture_reservation.h',
  'src/capture/capture_fs.h','standalone/build_viewer_file.py','standalone/build_path_session.py']
 r=dict(binary_sha256=sha(out/'VIEWFILE.EXE'),sources={n:sha(ROOT/n) for n in names},original_inputs=[],
  owner_segments=segments,owner_bytes=90,snapshot_bytes=84,state_segment=int(state[1],16),DGROUP_segment=int(group[1],16),
  scope=__doc__+' Standalone owner; no viewer UI/terminal dispatch or physical acceptance.')
 (out/'manifest.json').write_text(json.dumps(r,indent=2)+'\n');print('Built VIEWFILE.EXE',r['binary_sha256'])
if __name__=='__main__':main()
