#!/usr/bin/env python3
"""Observe real EXEC success/error and child exit codes before shell consumption."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True)
    source=ROOT/'standalone/dos_status_runner.asm'
    rows=[]
    for name,code,expected in [('zero',0,(0,0,0)),('error42',42,(0,0,42)),('missing',None,(1,2,0xff7e))]:
        folder=out/name
        folder.mkdir()
        subprocess.run(['nasm','-fbin',str(source),'-o',str(folder/'RUNSTAT.COM')],check=True)
        if code is not None:
            (folder/'TERMINAL.EXE').write_bytes(b'\xb8'+struct.pack('<H',0x4c00|code)+b'\xcd\x21')
        config=folder/'test.conf'
        config.write_text('[sdl]\noutput=surface\n[autoexec]\nmount c "'+str(folder)+'"\nmount d "'+str(folder)+'"\nc:\nRUNSTAT\nexit\n')
        with (folder/'dosbox.log').open('w') as log:
            subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],
                           env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),
                           stdout=log,stderr=log,check=True,timeout=15)
        observed=struct.unpack('<3H',(folder/'EXITCODE.BIN').read_bytes())
        assert observed==expected,(name,observed)
        rows.append(dict(case=name,status=observed))
    names=['standalone/dos_status_runner.asm','standalone/test_dos_status_runner.py']
    result=dict(passed=True,cases=rows,sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names},
                scope=__doc__+' Owned five-byte child fixtures and missing-file error. No application or physical acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS DOS status runner:',len(rows),'EXEC/exit cases')


if __name__=='__main__':main()
