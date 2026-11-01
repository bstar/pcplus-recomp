#!/usr/bin/env python3
"""Build the production translation identity publication owner for DOS8086."""
import hashlib,json,os,subprocess
from pathlib import Path
from build_phone_log_file import stable_header
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/xlt-resource-adoption'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 units=[('live','src/translation/xlt_live.c',[]),('reader','src/translation/xlt_dos.c',[]),('capture','src/capture/capture_file.c',[]),('reservation','src/capture/capture_reservation.c',[]),('fs','src/capture/capture_fs.c',['capture_fs_canonical=resource_real_canonical']),('paths','src/config/resource_path.c',[]),('diagnostic','standalone/xlt_resource_adoption_diagnostic.c',[])]
 flags=['-q','-bt=dos','-0','-ms','-s','-w4','-we','-zld','-dDIRECTORY_RESOURCE_ADOPTION','-dDIRECTORY_TRANSLATION_RESOURCES','-dTERMINAL_HOOK_INPUT']
 objects=[]
 for name,source,aliases in units:
  obj=name+'.obj';objects.append(obj)
  subprocess.run(['wcl','-c',*flags,*['-d'+a for a in aliases],'-fo='+obj,os.path.relpath(ROOT/source,OUT)],cwd=OUT,check=True);stable_header(OUT/obj,source)
 subprocess.run(['wcl',*flags,'-k8192','-fm=XLTADOPT.map','-fe=XLTADOPT.EXE',*objects],cwd=OUT,check=True)
 headers=['src/translation/xlt_live.h','src/translation/xlt_dos.h','src/translation/xlt_dos_fs.h','src/capture/capture_file.h','src/capture/capture_fs.h','src/capture/capture_reservation.h','src/config/resource_path.h']
 sources=[s for _,s,_ in units]+headers+['standalone/build_xlt_resource_adoption.py','standalone/build_phone_log_file.py'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 (OUT/'manifest.json').write_text(json.dumps(dict(original_inputs=[],binary_sha256=sha(OUT/'XLTADOPT.EXE'),objects={n:sha(OUT/n) for n in objects},sources={n:sha(ROOT/n) for n in sorted(set(sources))},flags=flags),indent=2)+'\n');print('Built XLTADOPT.EXE')
if __name__=='__main__':main()
