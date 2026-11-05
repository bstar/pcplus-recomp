#!/usr/bin/env python3
"""Build the source-only banked incremental viewer decoder diagnostic."""
import argparse,json,subprocess
from pathlib import Path
from build_path_session import ROOT,sha,object_segments

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we']
 units=[('decode','src/filesystem/viewer_decode.c',True,[]),
        ('boundary','standalone/viewer_decode_diagnostic.c',True,['-dVIEWER_DECODE_BOUNDARY']),
        ('diagnostic','standalone/viewer_decode_diagnostic.c',False,[])]
 for name,source,bank,extra in units:
  subprocess.run(['wcc',*flags,*(['-nt=FILE_CODE','-nc=FARCODE'] if bank else []),*extra,
    '-fo='+str(out/(name+'.obj')),str(ROOT/source)],cwd=out,check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fm=DECODE.map','-fe=DECODE.EXE',
                 *[name+'.obj' for name,_,_,_ in units]],cwd=out,check=True)
 segments=object_segments(out/'decode.obj')
 assert segments['FILE_CODE']['class']=='FARCODE'
 assert all(not s['bytes'] for n,s in segments.items() if n!='FILE_CODE'),segments
 names=['src/filesystem/viewer_decode.c','src/filesystem/viewer_decode.h',
        'standalone/viewer_decode_diagnostic.c','standalone/build_viewer_decode.py','standalone/build_path_session.py']
 r=dict(binary_sha256=sha(out/'DECODE.EXE'),sources={n:sha(ROOT/n) for n in names},
        original_inputs=[],decoder_segments=segments,state_bytes=26,
        scope=__doc__+' No application/UI, file handle, DOS service or physical acceptance.')
 (out/'manifest.json').write_text(json.dumps(r,indent=2)+'\n');print('Built DECODE.EXE',r['binary_sha256'])
if __name__=='__main__':main()
