#!/usr/bin/env python3
"""Actual parent reload quarantine after a reported close error, on owned DOS media."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import subprocess
from test_keymap_editor_dos import sha
from test_keymap_helper import image
from modem_fixtures import fixture
import test_connection_dos as lab

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('terminal','output'):
        parser.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args()
    parent=args.terminal.resolve();out=args.output.resolve()
    assert parent.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads(parent.with_name('manifest.json').read_text())
    assert manifest['experimental_keymap_editor'] and sha(parent)==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    out.mkdir(parents=True);runtime=out/'runtime';runtime.mkdir()
    for leaf in ('TERMINAL.EXE','PCLINE.OVL','PCMETA.OVL'):
        shutil.copyfile(parent.with_name(leaf),runtime/leaf)
    child=out/'arm.asm'
    child.write_text('BITS 16\nCPU 8086\nSEGMENT CODE public class=CODE use16\nglobal start\nstart:\n'
                     'mov ax,0d74ah\nmov bx,1\nint 2fh\ncmp ax,4b46h\njne fail\nmov ax,4c00h\nint 21h\n'
                     'fail: mov ax,4c7eh\nint 21h\nSEGMENT STACK stack class=STACK use16\nresb 256\n')
    subprocess.run(['nasm','-fobj',str(child),'-o',str(out/'arm.obj')],check=True)
    subprocess.run(['wlink','system','dos','option','quiet','option','start=start','name',str(runtime/'PCKEYMAP.EXE'),'file',str(out/'arm.obj')],check=True)
    observer=out/'KBCLOSE.COM'
    subprocess.run(['nasm','-fbin',str(ROOT/'standalone/keymap_close_fault.asm'),'-o',str(observer)],check=True)
    settings=bytearray(fixture())
    for offset,value in ((0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x3e4,7),(0x3e6,11),(0x3e8,113)):
        struct.pack_into('<H',settings,offset,value)
    base=image();lab.BINARY=runtime/'TERMINAL.EXE'
    result=lab.run(out.name,'success','p900 enter p3000 a-f8 p1600',prm=bytes(settings),
                   arguments='@D:\\TEST.PRM /D:CaseTest:23 /K:D:\\SYN.KBD COM1 19200 HARD',
                   files={'SYN.KBD':base,'KBCLOSE.COM':observer.read_bytes()},observer='KBCLOSE',
                   working_drive='d',cpu='8086',expected=14,timeout=25)
    drive=ROOT/'build/connection-dos'/out.name
    report=struct.unpack('<7H',(drive/'KBCLOSE.BIN').read_bytes())
    checks=dict(result['checks'])
    checks['one_real_close_and_one_reported_failure']=report==(0x4b46,0,1,1,0,1,1)
    checks['source_KBD_preserved']=(drive/'SYN.KBD').read_bytes()==base
    checks['fault_fixture_unchanged']=(drive/'KBCLOSE.COM').read_bytes()==observer.read_bytes()
    names=['standalone/keymap_close_fault.asm','standalone/test_keymap_close_return_dos.py',
           'standalone/test_keymap_editor_dos.py','standalone/test_keymap_helper.py',
           'standalone/test_connection_dos.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py']
    receipt=dict(passed=all(checks.values()),checks=checks,report=report,parent_sha256=sha(parent),
                 child_sha256=sha(runtime/'PCKEYMAP.EXE'),observer_sha256=sha(observer),
                 sources={name:sha(ROOT/name) for name in names},original_inputs=[],
                 scope='Owned DOS8086 TSR explicitly armed by fake helper; matches frozen SYN.KBD open, performs actual DOS close then reports error6. Parent must exit14 with source/hardware intact. TSR verifies restoration of its INT21/2F vectors. No application-memory or data mutation, actual failed-close resource retention, BBS or physical acceptance.')
    (out/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    assert receipt['passed'],checks
    print('PASS actual parent reload close-error quarantine14; source and vectors preserved')


if __name__=='__main__':main()
