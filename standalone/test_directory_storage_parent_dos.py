#!/usr/bin/env python3
"""Actual parent banked accounting, startup edit/save and resolved-owner EXEC."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import test_connection_dos as driver
from directory_fixtures import directory, prm
from test_directory_key_bindings_dos import actions

ROOT=driver.ROOT
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
CHILD='''BITS 16
CPU 8086
ORG 100h
mov dx,name
xor cx,cx
mov ah,3ch
int 21h
jc failed
mov bx,ax
mov dx,data
mov cx,7
mov ah,40h
int 21h
jc failed
cmp ax,7
jne failed
mov ah,3eh
int 21h
jc failed
mov ax,4c00h
int 21h
failed:
mov ax,4c01h
int 21h
name: db 'D:\\CHILD.OK',0
data: db 'EXEC-OK'
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal',type=Path,required=True)
    p.add_argument('--label',required=True)
    args=p.parse_args()
    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
    binary=args.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text())
    assert manifest['experimental_directory_storage'] and sha(binary)==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    out=ROOT/'build/directory-storage-parent'/args.label;out.mkdir(parents=True,exist_ok=False)
    (out/'child.asm').write_text(CHILD)
    subprocess.run(['nasm','-fbin',str(out/'child.asm'),'-o',str(out/'PROBE.COM')],check=True)
    raw=bytearray(prm(port=3,baud=5));struct.pack_into('<H',raw,0x188,5)
    struct.pack_into('<HH',raw,0x4e4,8,4)
    payload=directory(baud=5)
    driver.BINARY=binary
    cases=[]
    cases.append(driver.run('storage-accounting-'+args.label,'success','p900 enter p4500 a-x',
        directory=payload,prm=bytes(raw),arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1',
        com=3,irq=5,cpu='8086',working_drive='d'))
    edited=bytearray(payload);edited[250]=ord('Z')
    name='storage-edit-exec-'+args.label
    cases.append(driver.run(name,'success',
        'p500 e p400 s-z p120 f10 p600 enter p900 enter p4500 a-1 p1800 space p600 a-x',
        directory=payload,directory_expected=bytes(edited),prm=bytes(raw),
        arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /T:D:\\ACTIONS.KEY',
        com=3,irq=5,cpu='8086',working_drive='d',
        files={'PROBE.COM':(out/'PROBE.COM').read_bytes(),'ACTIONS.KEY':actions(b'D:\\PROBE.COM',1)}))
    marker=ROOT/'build/connection-dos'/name/'CHILD.OK'
    assert marker.read_bytes()==b'EXEC-OK','No successful child after guarded startup save'
    assert all(r['passed'] for r in cases)
    report=dict(passed=True,binary_sha256=sha(binary),cases=cases,
        resolved_owner_child_ran=True,marker_sha256=sha(marker),
        sources={n:sha(ROOT/n) for n in ['standalone/test_directory_storage_parent_dos.py',
            'standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py',
            'standalone/directory_test_support.py','standalone/test_directory_key_bindings_dos.py']},
        limitations=['Actual DOS parent/kernel banking and synthetic modem; physical hardware and live selection adoption remain open.'])
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS guarded parent accounting, startup save and subsequent DOS child')


if __name__=='__main__':main()
