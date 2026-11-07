#!/usr/bin/env python3
"""Build a source-only foreground keyboard-mapping helper."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES=['src/key_mapping/keymap_front.c','src/key_mapping/keymap_screen.c','src/key_mapping/keymap_field.c','src/key_mapping/keymap_text.c','src/key_mapping/kbd_editor_file.c','src/key_mapping/key_file_fs.c','src/directory/directory_replace.c','src/directory/directory_replace_fs.c']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-os','-w4','-we','-k4096','-fm=PCKEYMAP.map','-fe=PCKEYMAP.EXE',*[str(ROOT/n) for n in SOURCES]],cwd=out,check=True)
 names=SOURCES+['standalone/build_keymap_helper.py','src/key_mapping/keymap_screen.h','src/key_mapping/keymap_field.h','src/key_mapping/keymap_text.h','src/key_mapping/kbd_editor_file.h','src/key_mapping/key_file_fs.h','src/directory/directory_replace.h','src/directory/directory_replace_fs.h','src/directory/directory_dos.h']
 result=dict(passed=True,original_inputs=[],binary_sha256=hashlib.sha256((out/'PCKEYMAP.EXE').read_bytes()).hexdigest(),sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},scope='Build only; runtime/persistence/parent admission remain separate.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
