#!/usr/bin/env python3
"""Exercise length-preserving KBD transactions at actual DOS IO boundaries."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True)
    sources=['src/key_mapping/kbd_editor_file.c','src/key_mapping/key_file_fs.c','src/directory/directory_replace.c',
             'src/directory/directory_replace_fs.c','standalone/kbd_editor_faults.c','standalone/kbd_editor_prefix_driver.c']
    flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-os','-w4','-we','-i='+str(ROOT/'src/key_mapping'),'-i='+str(ROOT/'standalone')]
    objects=[]
    for name in sources:
        obj=out/(Path(name).stem+'.obj')
        extra=['-dkey_file_'+n+'=key_real_'+n for n in ('attr','open','create','read','write','close','rename','delete')] if name.endswith('key_file_fs.c') else []
        subprocess.run(['wcc',*flags,*extra,'-fo='+str(obj),str(ROOT/name)],check=True);objects.append(str(obj))
    subprocess.run(['wcl',*flags,'-k4096','-fe=KBDPFX.EXE',*objects],cwd=out,check=True)
    (out/'LAB').mkdir()
    (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nKBDPFX >RESULT.TXT\nexit\n')
    with (out/'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],
                       env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=100)
    text=(out/'RESULT.TXT').read_text()
    assert '33 LENGTHS; 57 SAVE FAULT CASES; 6 LENGTH RACES' in text,text
    names=sources+['src/key_mapping/kbd_editor_prefix.h','src/key_mapping/kbd_editor_file.h','src/key_mapping/key_file_fs.h',
                   'src/directory/directory_replace.h','src/directory/directory_replace_fs.h','src/directory/directory_dos.h',
                   'standalone/key_editor_faults.h','standalone/test_kbd_editor_prefix.py']
    result=dict(passed=True,cpu='8086',transcript=text.strip(),original_inputs=[],
                sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names},
                scope='Actual DOS1..33-profile file load/save, exact EOF/preserved suffixes,57 real IO save-fault cases,6 concurrent length-change refusals, failed-load nonpublication and invalid lengths. No crash atomicity, external locking or physical acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(text)


if __name__=='__main__':main()
