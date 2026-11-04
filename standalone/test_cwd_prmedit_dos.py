#!/usr/bin/env python3
"""Actual production PRMEDIT opens startup PRM after PROGRAM changes real CWD."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import test_connection_dos as harness
from directory_fixtures import prm

ROOT = harness.ROOT
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
EXPECTED_EDITOR = '0a8452e70e10514fd03131dcf096283baca7bc7955e4883a380861e5bebef26e'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal',type=Path,required=True)
    p.add_argument('--editor',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args();binary=a.terminal.resolve();editor=a.editor.resolve();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    assert sha(editor)==EXPECTED_EDITOR
    manifest=json.loads((binary.parent/'manifest.json').read_text())
    assert sha(binary)==manifest['binary_sha256'] and manifest['experimental_cwd_identities']
    out.mkdir(parents=True);package=out/'package';package.mkdir()
    shutil.copyfile(binary,package/'TERMINAL.EXE');shutil.copyfile(editor,package/'PRMEDIT.EXE')
    child=ROOT/'standalone/cwd_identity_child.c'
    for leaf,flag in [('CHDIR.EXE','-dCWD_CHANGE'),('DECOY.EXE','-dCWD_DECOY')]:
        subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k4096',flag,
                        '-fe='+leaf,str(child)],cwd=package,check=True)
    watcher=out/'PRMWATCH.COM'
    subprocess.run(['nasm','-fbin',str(ROOT/'standalone/cwd_prmedit_watch.asm'),'-o',str(watcher)],check=True)
    settings=bytearray(prm(port=3,baud=5));struct.pack_into('<H',settings,0x188,5)
    for at,value in [(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),
                     (0x1bc,0),(0x1be,0),(0x1e6,0)]:struct.pack_into('<H',settings,at,value)
    settings=bytes(settings);decoy=bytearray(settings);struct.pack_into('<H',decoy,0,1);decoy=bytes(decoy)
    keys=bytearray(540)
    for i in range(10):struct.pack_into('<H',keys,i*54,3)
    command=b'D:\\CHDIR.EXE';struct.pack_into('<H',keys,0,1);keys[2:2+len(command)]=command
    files={'TEST.KEY':bytes(keys),'CHDIR.EXE':(package/'CHDIR.EXE').read_bytes(),
           'OTHER/TEST.PRM':decoy,'OTHER/PRMEDIT.EXE':(package/'DECOY.EXE').read_bytes(),
           'PRMWATCH.COM':watcher.read_bytes()}
    name=out.name;drive=ROOT/'build/connection-dos'/name;assert not drive.exists()
    harness.BINARY=package/'TERMINAL.EXE'
    keyboard='p900 enter p3500 a-1 p1600 space p900 a-s p2200 escape p1200 space p700 r e a d y enter p1200 a-x'
    base=harness.run(name,'success',keyboard,prm=settings,arguments='@TEST.PRM /T:TEST.KEY /D:CaseTest:23',
                     com=3,irq=5,cpu='8086',working_drive='d',files=files,observer='PRMWATCH',timeout=30,
                     online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-REAL-SETUP\x1b[6n'),))
    observed=(drive/'PRMVIEW.BIN').read_bytes();assert len(observed)==4071
    magic,flags,ticks=struct.unpack_from('<3H',observed);frame=observed[6:4006]
    text=frame[::2];wire=(drive/'serial.bin').read_bytes();screen=(drive/'SCREEN.BIN').read_bytes()
    checks=dict(base['checks'])
    checks.update(observer_captured_stable_editor_and_restored_vector=magic==0x4349 and flags==3 and ticks>2,
                  production_editor_title=text[:80].startswith(b' PCPlus / SYSTEM CONFIGURATION'),
                  production_editor_serial_page=text[3*80+2:3*80+8]==b'SERIAL',
                  production_editor_port_label=text[5*80+2:5*80+6]==b'Port',
                  production_editor_startup_COM3=text[5*80+25:5*80+28]==b'3  ',
                  production_editor_discard_footer=b'Esc Discard' in text[23*80:24*80],
                  actual_DOS_chdir_observed=(drive/'CWDMOVED.TXT').read_text()=='before=D:\\\nafter=D:\\OTHER\n',
                  child_created_witness=(drive/'OTHER/WITNESS').is_dir(),
                  production_editor_restored_changed_CWD=observed[4006]==3 and observed[4007:].split(b'\0')[0]==b'OTHER',
                  decoy_helper_not_executed=not (drive/'DECOY.TXT').exists(),
                  post_editor_keyboard_delivered=wire.count(b'ready\r')==1,
                  post_editor_UART_query_replied=b'\x1b[3;17R' in wire,
                  post_editor_UART_input_rendered=screen[320:352:2]==b'AFTER-REAL-SETUP',
                  no_editor_recovery_files=not any((folder/leaf).exists() for folder in (drive,drive/'OTHER') for leaf in ('PRMEDIT.BAK','PRMEDIT.$$$')))
    (out/'editor-screen.txt').write_text('\n'.join(text[i*80:(i+1)*80].decode('cp437') for i in range(25))+'\n')
    sources=['standalone/test_cwd_prmedit_dos.py','standalone/cwd_prmedit_watch.asm',
             'standalone/cwd_identity_child.c','standalone/test_connection_dos.py','standalone/test_terminal.py',
             'standalone/directory_fixtures.py','standalone/directory_test_support.py',
             'standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py']
    report=dict(passed=all(checks.values()),checks=checks,binary_sha256=sha(binary),editor_sha256=sha(editor),
                observer=dict(flags=flags,ticks=ticks),sources={n:sha(ROOT/n) for n in sources},
                artifacts={str(f.relative_to(drive)):sha(f) for f in drive.rglob('*') if f.is_file()},original_inputs=[],
                scope=__doc__+' DOSBox-X8086 COM3/IRQ5, synthetic modem peer and owned files. Real production editor opens and displays COM3 from startup PRM after CWD moves beside COM2 decoy; Escape cancels, files stay unchanged, editor restores changed CWD, late UART/keyboard/query and final hardware restoration pass. Passive INT1C reads VGA only; DOS collection/vector restore occurs after terminal exit. No editor save/adoption, physical machine, original PCSETUP or Alt-F7 UI acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS' if report['passed'] else 'FAIL',{k:v for k,v in checks.items() if not v},flush=True)
    assert report['passed'],report

if __name__=='__main__':main()
