#!/usr/bin/env python3
"""Actual connected parent creates an absent KBD or retains its frozen selection."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import test_connection_dos as lab
from modem_fixtures import fixture
from package_connection_test import terminal_companions,sha
from test_keymap_helper import image,changed

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('terminal','helper','output'):parser.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args();parent=args.terminal.resolve();helper=args.helper.resolve();out=args.output.resolve()
    assert parent.is_relative_to(ROOT/'build') and helper.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads(parent.with_name('manifest.json').read_text());proof=json.loads(helper.with_name('result.json').read_text())
    assert manifest['experimental_keymap_editor'] and sha(parent)==manifest['binary_sha256']
    assert proof['passed'] and proof['original_inputs']==[] and sha(helper)==proof['binary_sha256']
    for name,digest in {**manifest['sources'],**proof['sources']}.items():assert sha(ROOT/name)==digest,name
    companions,sources=terminal_companions(parent,manifest);out.mkdir(parents=True);runtime=out/'runtime';runtime.mkdir()
    for name,path in {'TERMINAL.EXE':parent,'PCKEYMAP.EXE':helper,**companions}.items():shutil.copyfile(path,runtime/name)
    products={p.name:sha(p) for p in runtime.iterdir()};lab.BINARY=runtime/'TERMINAL.EXE'
    settings=bytearray(fixture())
    for at,value in ((0x4e4,8),(0x4e6,4),(0x194,6),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x3e4,7),(0x3e6,11),(0x3e8,113)):
        struct.pack_into('<H',settings,at,value)
    rows=[];edit='f1 p100 tab n e w enter p200 '
    for case in ('create-selected','discard-selected','create-other'):
        label=out.name+'-'+case;drive=ROOT/'build/connection-dos'/label;assert not drive.exists()
        files={};arguments='@D:\\TEST.PRM /D:CaseTest:23 COM1 19200 HARD';opening=''
        if case=='create-other':
            files['SYN.KBD']=image()[:7*948];arguments+=' /K:D:\\SYN.KBD';opening='a-o p150 n e w enter p350 '
        action='escape p200 n p500 space' if case=='discard-selected' else 'a-s p500 escape'
        ending='p1000 '+('' if case=='discard-selected' else 'f1 p250 ')+'r e a d y p500 a-x'
        r=lab.run(label,'success','p900 enter p3000 a-f8 p1600 '+opening+edit+action+' '+ending,
            prm=bytes(settings),arguments=arguments,files=files,cpu='8086',working_drive='d',timeout=35)
        checks=dict(r['checks']);wire=(drive/'serial.bin').read_bytes();new_path=drive/('NEW.KBD' if case=='create-other' else 'PCPLUS.KBD')
        checks.update(ordinary_keys_resume=b'ready' in wire,
            products_unchanged=all(sha(runtime/name)==digest for name,digest in products.items()),
            no_staging=not (drive/'KBDSTG.$$$').exists() and not (drive/'KBDBAK.$$$').exists())
        if case=='discard-selected':checks['discard_creates_nothing']=not new_path.exists()
        else:
            checks['exact_new_file']=new_path.is_file() and new_path.read_bytes()==changed(bytes(31284))
            checks['frozen_live_selection']=((b'P0616' in wire and b'new' not in wire) if case=='create-other' else b'new' in wire)
        row=dict(case=case,passed=all(checks.values()),checks=checks,raw_result=str((drive/'result.json').relative_to(ROOT)))
        (out/(case+'.json')).write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
        assert row['passed'],(case,[name for name,value in checks.items() if not value]);print('PASS parent new file:',case,flush=True)
    names=['standalone/test_keymap_create_parent.py','standalone/test_connection_dos.py','standalone/modem_fixtures.py','standalone/test_keymap_helper.py','standalone/package_connection_test.py']
    result=dict(passed=True,parent_sha256=sha(parent),helper_sha256=sha(helper),products=products,cases=rows,cpu='8086',original_inputs=[],
        sources={**sources,**{name:sha(ROOT/name) for name in names}},scope=__doc__+' Real DOS/BIOS/files/UART and maintained parent/helper; synthetic serial modem, no physical/private configuration acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
