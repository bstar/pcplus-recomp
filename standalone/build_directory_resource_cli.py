#!/usr/bin/env python3
"""Build original CLI identity capture through the actual terminal adapter."""
import hashlib,json,os,subprocess
from pathlib import Path
from build_phone_log_file import stable_header
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/directory-resource-cli'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 units=[
 ('cli','src/directory/directory_resource_cli.c',[]),
 ('adapter','src/terminal/resource_cli_bind.c',[]),
 ('resources','src/directory/directory_resources.c',[]),
 ('keymap','src/key_mapping/keymap_dos.c',[]),
 ('actions','src/key_mapping/key_actions_dos.c',[]),
 ('seek','src/key_mapping/keymap_dos_fs.c',[]),
 ('paths','src/config/resource_path.c',[]),
 ('live','src/directory/directory_live.c',[]),
 ('directory','src/directory/directory_dos.c',[]),
 ('terminal','src/config/terminal_import.c',[]),
 ('modem','src/config/modem_import.c',[]),
 ('prm','src/config/prm_dos.c',[]),
 ('capture','src/capture/capture_file.c',[]),
 ('reservations','src/capture/capture_reservation.c',[]),
 ('fs','src/capture/capture_fs.c',['capture_fs_canonical=cli_real_canonical']),
 ('diagnostic','standalone/directory_resource_cli_diagnostic.c',[])]
 flags=['-q','-bt=dos','-0','-ms','-s','-w4','-we','-zld','-dDIRECTORY_KEY_BINDINGS',
 '-dTERMINAL_CUSTOM_IRQ','-dKEY_RESOURCE_PRIVATE_READS','-dCAPTURE_FIXED_RESERVATION','-i=../../src/config']
 objects=[]
 for name,source,aliases in units:
  obj=name+'.obj';objects.append(obj)
  subprocess.run(['wcl','-c',*flags,*['-d'+a for a in aliases],'-fo='+obj,os.path.relpath(ROOT/source,OUT)],cwd=OUT,check=True)
  stable_header(OUT/obj,source)
 asm='reconstruction/directory_dial/bounded.asm';objects.append('number.obj')
 subprocess.run(['nasm','-fobj',asm,'-o',str(OUT/'number.obj')],cwd=ROOT,check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fm=CLI.map','-fe=CLI.EXE',*objects],cwd=OUT,check=True)
 headers=['src/directory/directory_resource_cli.h','src/directory/directory_resources.h',
 'src/directory/directory_live.h','src/directory/directory_dos.h','src/config/resource_path.h',
 'src/config/terminal_import.h','src/config/modem_import.h','src/config/prm_dos.h','src/config/irq_policy.h',
 'src/key_mapping/keymap_dos.h','src/key_mapping/key_actions_dos.h','src/key_mapping/keymap_dos_fs.h',
 'src/capture/capture_file.h','src/capture/capture_fs.h','src/capture/capture_reservation.h']
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 sources=[s for _,s,_ in units]+headers+[asm,'standalone/build_directory_resource_cli.py','standalone/build_phone_log_file.py']
 manifest=dict(kind='source-only-original-CLI-resource-identities',original_inputs=[],binary_sha256=sha(OUT/'CLI.EXE'),
  objects={o:sha(OUT/o) for o in objects},sources={s:sha(ROOT/s) for s in sorted(set(sources))},snapshot_bytes=138,
  limitations=['Actual startup wrapper and request/staging component; parent live adoption/lease/UART commit remain open.'])
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built CLI.EXE',manifest['binary_sha256'])
if __name__=='__main__':main()
