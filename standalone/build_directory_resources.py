#!/usr/bin/env python3
"""Source-only DOS16 staged KEY/KBD resource transaction and fault witnesses."""
import hashlib,json,os,subprocess
from pathlib import Path
from build_phone_log_file import stable_header
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/directory-resources'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 units=[
 ('resources','src/directory/directory_resources.c',['capture_file_release=resource_test_release']),
 ('keymap','src/key_mapping/keymap_dos.c',['_dos_open=resource_test_open','_dos_close=resource_test_close']),
 ('actions','src/key_mapping/key_actions_dos.c',['_dos_open=resource_test_open','_dos_close=resource_test_close']),
 ('seek','src/key_mapping/keymap_dos_fs.c',[]),
 ('paths','src/config/resource_path.c',[]),
 ('live','src/directory/directory_live.c',[]),
 ('directory','src/directory/directory_dos.c',[]),
 ('terminal','src/config/terminal_import.c',[]),
 ('modem','src/config/modem_import.c',[]),
 ('prm','src/config/prm_dos.c',[]),
 ('capture','src/capture/capture_file.c',[]),
 ('reservations','src/capture/capture_reservation.c',[]),
 ('fs','src/capture/capture_fs.c',['capture_fs_canonical=resource_real_canonical','capture_fs_attributes=resource_real_attributes']),
 ('diagnostic','standalone/directory_resources_diagnostic.c',[])]
 flags=['-q','-bt=dos','-0','-ms','-s','-w4','-we','-zld',
 '-dDIRECTORY_KEY_BINDINGS','-dTERMINAL_CUSTOM_IRQ','-dKEY_RESOURCE_PRIVATE_READS','-dCAPTURE_FIXED_RESERVATION',
 '-i=../../src/config']
 objects=[]
 for name,source,aliases in units:
  obj=name+'.obj';objects.append(obj)
  subprocess.run(['wcl','-c',*flags,*['-d'+a for a in aliases],'-fo='+obj,os.path.relpath(ROOT/source,OUT)],cwd=OUT,check=True)
  stable_header(OUT/obj,source)
 asm='reconstruction/directory_dial/bounded.asm';objects.append('number.obj')
 subprocess.run(['nasm','-fobj',asm,'-o',str(OUT/'number.obj')],cwd=ROOT,check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fm=RESOURCES.map','-fe=RESOURCE.EXE',*objects],cwd=OUT,check=True)
 headers=['src/directory/directory_resources.h','src/directory/directory_live.h',
 'src/directory/directory_dos.h','src/config/resource_path.h','src/config/terminal_import.h',
 'src/config/modem_import.h','src/config/prm_dos.h','src/config/irq_policy.h',
 'src/key_mapping/keymap_dos.h','src/key_mapping/key_actions_dos.h','src/key_mapping/keymap_dos_fs.h',
 'src/capture/capture_file.h','src/capture/capture_fs.h','src/capture/capture_reservation.h']
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 sources=[s for _,s,_ in units]+headers+[asm,'standalone/build_directory_resources.py','standalone/build_phone_log_file.py']
 report=dict(kind='source-only-staged-directory-KEY-KBD-resources',original_inputs=[],
  binary_sha256=sha(OUT/'RESOURCE.EXE'),objects={o:sha(OUT/o) for o in objects},
  sources={s:sha(ROOT/s) for s in sorted(set(sources))},flags=flags,request_bytes=248,bundle_bytes=1624,snapshot_bytes=142,
  limitations=['Component only; live CLI binding, lease and selection/UART adoption remain open.',
   'No translation/script staging, external-writer lock or physical hardware acceptance.'])
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Built RESOURCE.EXE',report['binary_sha256'])
if __name__=='__main__':main()
