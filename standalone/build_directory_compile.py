#!/usr/bin/env python3
"""Compile-owner component with declared DOS spawning/fault adapters."""
import hashlib,json,os,subprocess
from pathlib import Path
from build_phone_log_file import stable_header
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/directory-compile'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 units=[('compile','src/directory/directory_compile.c',['capture_file_release=compile_test_release']),('script','src/directory/directory_script.c',['xlt_fs_open=compile_test_open','xlt_fs_read=compile_test_read','xlt_fs_close=compile_test_close']),('capture','src/capture/capture_file.c',[]),('reservations','src/capture/capture_reservation.c',[]),('fs','src/capture/capture_fs.c',[]),('paths','src/config/resource_path.c',[]),('diagnostic','standalone/directory_compile_diagnostic.c',[])]
 flags=['-q','-bt=dos','-0','-ms','-s','-w4','-we','-zld','-dDIRECTORY_TRANSLATION_RESOURCES','-dDIRECTORY_SCRIPT_RESOURCES','-i=../../src/config']
 objects=[]
 for name,source,aliases in units:
  obj=name+'.obj';objects.append(obj);subprocess.run(['wcl','-c',*flags,*['-d'+a for a in aliases],'-fo='+obj,os.path.relpath(ROOT/source,OUT)],cwd=OUT,check=True);stable_header(OUT/obj,source)
 subprocess.run(['wcl',*flags,'-k8192','-fm=DCOMPILE.map','-fe=DCOMPILE.EXE',*objects],cwd=OUT,check=True)
 source='standalone/directory_compile_fault_child.c';subprocess.run(['wcl',*flags,'-fm=FAULT.map','-fe=FAULT.EXE',os.path.relpath(ROOT/source,OUT)],cwd=OUT,check=True)
 headers=['src/directory/directory_compile.h','src/directory/directory_script.h','src/directory/directory_resources.h','src/key_mapping/keymap_dos.h','src/key_mapping/key_actions_dos.h','src/translation/xlt_dos_fs.h','src/capture/capture_file.h','src/capture/capture_fs.h','src/capture/capture_reservation.h','src/config/resource_path.h','src/process/dos_exec.h']
 sources=[s for _,s,_ in units]+headers+[source,'standalone/build_directory_compile.py','standalone/build_phone_log_file.py'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 (OUT/'manifest.json').write_text(json.dumps(dict(original_inputs=[],binary_sha256=sha(OUT/'DCOMPILE.EXE'),fault_child_sha256=sha(OUT/'FAULT.EXE'),objects={n:sha(OUT/n) for n in objects},sources={n:sha(ROOT/n) for n in sorted(set(sources))},flags=flags),indent=2)+'\n');print('Built DCOMPILE.EXE')
if __name__=='__main__':main()
