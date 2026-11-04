#!/usr/bin/env python3
"""Build source-only original path helper and guarded DOS path diagnostics."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 native=ROOT/'reconstruction/file_path/change.asm';proof=json.loads((native.parent/'provenance.json').read_text())
 subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(native),'-o',str(out/'change.bin')],check=True)
 assert sha(out/'change.bin')==proof['sha256'] and (out/'change.bin').stat().st_size==proof['bytes']
 subprocess.run(['nasm','-fobj','-DFILE_PATH_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(native),'-o',str(out/'change.obj')],check=True)
 aliases=['path_native_change=path_native_real','path_current_drive=path_drive_real','path_select_drive=path_select_real','path_getcwd=path_cwd_real']
 subprocess.run(['nasm','-fobj',*['-D_'+n.replace('=','=_') for n in aliases],str(ROOT/'src/filesystem/path_kernel.asm'),'-o',str(out/'kernel.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fm=PATH.map','-fe=PATH.EXE',str(ROOT/'src/filesystem/path_owner.c'),str(ROOT/'standalone/path_owner_diagnostic.c'),'change.obj','kernel.obj'],cwd=out,check=True)
 names=['reconstruction/file_path/change.asm','reconstruction/file_path/provenance.json','reconstruction/uart/encodings.inc','src/filesystem/path_owner.h','src/filesystem/path_owner.c','src/filesystem/path_kernel.asm','standalone/path_owner_diagnostic.c','standalone/build_path_owner.py']
 r={'kind':'source-only-file-path-owner-diagnostic','binary_sha256':sha(out/'PATH.EXE'),'sources':{n:sha(ROOT/n) for n in names},'native_bytes':proof['bytes'],'original_inputs':[],'limitations':['Not a terminal/menu integration or an original AltF7 UI contract.','Verification/rollback faults are explicit test-only kernel-boundary wrappers.']}
 (out/'manifest.json').write_text(json.dumps(r,indent=2)+'\n');print('Built PATH.EXE',r['binary_sha256'])

if __name__=='__main__':main()
