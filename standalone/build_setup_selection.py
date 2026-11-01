#!/usr/bin/env python3
"""Build the frozen selection handoff with production setup/DOS code."""
import hashlib,json,os,subprocess
from pathlib import Path
from build_phone_log_file import stable_header
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/setup-selection'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 names=['src/config/live_setup_owner.c','src/config/live_configuration.c','src/config/terminal_import.c','src/config/modem_import.c','src/config/transfer_import.c','src/config/prm_dos.c','src/directory/directory_live.c','src/directory/directory_dos.c','src/capture/capture_file.c','src/capture/capture_reservation.c','src/capture/capture_fs.c','standalone/setup_selection_diagnostic.c']
 flags=['-q','-bt=dos','-0','-ms','-s','-w4','-we','-zld','-dDIRECTORY_RESOURCE_ADOPTION','-dTERMINAL_DIRECTORY_RETIREMENT','-dTERMINAL_CUSTOM_IRQ','-dDIRECTORY_KEY_BINDINGS','-i=../../src/config','-i=../../src/directory']
 objects=[]
 for i,source in enumerate(names):
  obj=f'unit{i:02}.obj';objects.append(obj)
  aliases=[] if source.startswith('standalone/') else ['_dos_open=selection_open','_dos_read=selection_read','_dos_close=selection_close']
  if source=='src/capture/capture_fs.c':aliases+=['capture_fs_canonical=selection_real_canonical']
  subprocess.run(['wcl','-c',*flags,*['-d'+a for a in aliases],'-fo='+obj,os.path.relpath(ROOT/source,OUT)],cwd=OUT,check=True);stable_header(OUT/obj,source)
 asm=['src/terminal/setup_expand.asm','reconstruction/modem_commands/bounded.asm','reconstruction/modem_commands/expand.asm','reconstruction/directory_dial/bounded.asm']
 for i,source in enumerate(asm):
  obj=f'asm{i:02}.obj';objects.append(obj);subprocess.run(['nasm','-fobj','-DMODEM_COMMANDS_OMF','-Ireconstruction/uart/',source,'-o',str(OUT/obj)],cwd=ROOT,check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fm=SELECT.map','-fe=SELECT.EXE',*objects],cwd=OUT,check=True)
 headers=['src/config/live_setup_owner.h','src/config/live_configuration.h','src/config/terminal_import.h','src/config/modem_import.h','src/config/transfer_import.h','src/config/prm_dos.h','src/config/irq_policy.h','src/directory/directory_live.h','src/directory/directory_dos.h','src/capture/capture_file.h','src/capture/capture_reservation.h','src/capture/capture_fs.h']
 sources=names+asm+headers+['reconstruction/uart/encodings.inc']+['standalone/build_setup_selection.py','standalone/build_phone_log_file.py'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 (OUT/'manifest.json').write_text(json.dumps(dict(original_inputs=[],binary_sha256=sha(OUT/'SELECT.EXE'),objects={n:sha(OUT/n) for n in objects},sources={n:sha(ROOT/n) for n in sorted(set(sources))},flags=flags),indent=2)+'\n');print('Built SELECT.EXE')
if __name__=='__main__':main()
