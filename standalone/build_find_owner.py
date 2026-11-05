#!/usr/bin/env python3
"""Build the original-free private-DTA listing component diagnostic."""
import argparse,json,re,subprocess
from pathlib import Path
from build_path_session import ROOT,sha,object_segments

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we']
 for name,source,bank in [('owner','src/filesystem/find_owner.c',True),('diagnostic','standalone/find_owner_diagnostic.c',False)]:
  subprocess.run(['wcc',*flags,*(['-nt=FILE_CODE','-nc=FARCODE'] if bank else []),'-fo='+str(out/(name+'.obj')),str(ROOT/source)],cwd=out,check=True)
 for name,source in [('kernel','src/filesystem/find_kernel.asm'),('probe','standalone/find_owner_probe.asm')]:
  subprocess.run(['nasm','-fobj',str(ROOT/source),'-o',str(out/(name+'.obj'))],check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fm=FIND.map','-fe=FIND.EXE','owner.obj','kernel.obj','diagnostic.obj','probe.obj'],cwd=out,check=True)
 segments=object_segments(out/'owner.obj');assert all(not s['bytes'] for n,s in segments.items() if n!='FILE_CODE'),segments
 assert segments['FILE_CODE']['class']=='FARCODE'
 listing=(out/'FIND.map').read_text();symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 group=re.search(r'^DGROUP\s+([0-9a-f]+):([0-9a-f]+)',listing,re.M|re.I);assert group
 assert symbols['_file_find_storage'][0]!=int(group[1],16)
 names=['src/filesystem/find_owner.c','src/filesystem/find_owner.h','src/filesystem/find_kernel.asm','standalone/find_owner_diagnostic.c','standalone/find_owner_probe.asm','standalone/build_find_owner.py','standalone/build_path_session.py']
 r=dict(binary_sha256=sha(out/'FIND.EXE'),sources={n:sha(ROOT/n) for n in names},original_inputs=[],owner_segments=segments,state=symbols['_file_find_storage'],DGROUP=int(group[1],16),scope=__doc__+' Not linked into the terminal; runtime and full file-command UI/ownership acceptance remain separate.')
 (out/'manifest.json').write_text(json.dumps(r,indent=2)+'\n');print('Built FIND.EXE',r['binary_sha256'])
if __name__=='__main__':main()
