#!/usr/bin/env python3
"""Build exact recovered GET source and exhaust its numeric filter in DOS8086."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    fixture=ROOT/'standalone/fixtures/aspect_get_native.json';baseline=json.loads(fixture.read_text());source=ROOT/'src/aspect/get_native.asm'
    subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/','-DASPECT_GET_FLAT',str(source),'-o',str(out/'GET.BIN')],check=True)
    assert (out/'GET.BIN').stat().st_size==baseline['bytes'] and sha(out/'GET.BIN')==baseline['sha256']
    subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(out/'get.obj')],check=True)
    subprocess.run(['nasm','-fobj',str(ROOT/'standalone/aspect_get_filter_stubs.asm'),'-o',str(out/'stubs.obj')],check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-fm=FILTER.MAP','-fe=FILTER.EXE',str(ROOT/'standalone/aspect_get_filter_driver.c'),'get.obj','stubs.obj'],cwd=out,check=True)
    (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "'+str(out)+'"\nc:\nFILTER >FILTER.OUT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with (out/'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
    transcript=(out/'FILTER.OUT').read_text().strip()
    assert transcript=='GET FILTER cases=65536 errors=0' and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),transcript
    names=['src/aspect/get_native.asm','reconstruction/uart/encodings.inc','standalone/fixtures/aspect_get_native.json','standalone/build_aspect_get_native.py','standalone/aspect_get_filter_stubs.asm','standalone/aspect_get_filter_driver.c']
    result=dict(passed=True,native_bytes=baseline['bytes'],native_sha256=sha(out/'GET.BIN'),object_sha256=sha(out/'get.obj'),diagnostic_sha256=sha(out/'FILTER.EXE'),transcript=transcript,cpu='8086',original_inputs=[],sources={name:sha(ROOT/name) for name in names},
        scope=__doc__+' Whole566-byte static identity and linked real DOS filter only; bell is a counter, other service stubs are not exercised. No shared-owner/runtime/compiler integration or real field/UI/serial acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(transcript)

if __name__=='__main__':main()
