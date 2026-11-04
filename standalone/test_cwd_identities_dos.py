#!/usr/bin/env python3
"""Real DOS8086 PROGRAM chdir, frozen setup identities and DIR accounting."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import test_connection_dos as harness
from directory_fixtures import directory, prm

ROOT = harness.ROOT
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); binary = a.terminal.resolve(); out = a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    manifest = json.loads((binary.parent/'manifest.json').read_text())
    assert sha(binary) == manifest['binary_sha256']
    assert manifest['experimental_cwd_identities'] and manifest['experimental_original_keys']
    out.mkdir(parents=True); package = out/'package'; package.mkdir()
    shutil.copyfile(binary, package/'TERMINAL.EXE')
    source = ROOT/'standalone/cwd_identity_child.c'
    for leaf, flags in [('CHDIR.EXE',['-dCWD_CHANGE']), ('DECOY.EXE',['-dCWD_DECOY']), ('PRMEDIT.EXE',[])]:
        subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k4096',*flags,
                        '-fe='+leaf,str(source)],cwd=package,check=True)
    settings = bytearray(prm(port=3,baud=5))
    struct.pack_into('<H',settings,0x188,5)
    for at,value in [(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),
                     (0x1bc,0),(0x1be,0),(0x1e6,0)]:
        struct.pack_into('<H',settings,at,value)
    settings = bytes(settings)
    decoy = bytearray(settings);struct.pack_into('<H',decoy,0x1ae,30);decoy = bytes(decoy)
    book = directory(port=3,baud=5)
    keys = bytearray(540)
    for i in range(10):struct.pack_into('<H',keys,i*54,3)
    command = b'D:\\CHDIR.EXE'
    struct.pack_into('<H',keys,0,1);keys[2:2+len(command)] = command
    cases = []
    harness.BINARY = package/'TERMINAL.EXE'
    for mode, setup_key in [('startup',None),('plain','a-s'),('directory','a-p')]:
        name = out.name+'-'+mode
        drive = ROOT/'build/connection-dos'/name
        assert not drive.exists()
        files = {'TEST.KEY':bytes(keys),'CHDIR.EXE':(package/'CHDIR.EXE').read_bytes(),
                 'PCPLUS.XLT':bytes(range(256)), 'OTHER/TEST.PRM':decoy,
                 'OTHER/TEST.DIR':book, 'OTHER/PCPLUS.XLT':bytes(reversed(range(256))),
                 'OTHER/PRMEDIT.EXE':(package/'DECOY.EXE').read_bytes()}
        arguments = '@TEST.PRM /T:TEST.KEY'+(' /S' if mode=='startup' else '')+(' /E:TEST.DIR /N:1' if mode=='directory' else ' /D:CaseTest:23')
        keyboard = 'p900 enter p3500 '+('a-1 p1600 space p900 '+setup_key+' p1600 space p700 ' if setup_key else '')+'r e a d y enter p1200 a-x'
        base = harness.run(name,'success',keyboard,prm=settings,directory=book if mode=='directory' else None,
                           arguments=arguments,com=3,irq=5,cpu='8086',working_drive='d',files=files,timeout=30,
                           online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-CWD-SETUP\x1b[6n'),))
        wire = (drive/'serial.bin').read_bytes();screen = (drive/'SCREEN.BIN').read_bytes()
        setup = (drive/'SETUP.TXT').read_text() if (drive/'SETUP.TXT').exists() else ''
        cwd = (drive/'CWDMOVED.TXT').read_text() if (drive/'CWDMOVED.TXT').exists() else ''
        checks = dict(base['checks'])
        checks.update(absolute_startup_PRM_argument='argument=D:\\TEST.PRM\n' in setup,
                      sibling_setup_executable='program=C:\\PRMEDIT.EXE\n' in setup,
                      setup_in_expected_CWD=('cwd=D:\\\n' if mode=='startup' else 'cwd=D:\\OTHER\n') in setup,
                      setup_read_original_PRM=(drive/'PRMSEEN.BIN').exists() and (drive/'PRMSEEN.BIN').read_bytes()==settings,
                      decoy_helper_not_executed=not (drive/'DECOY.TXT').exists(),
                      post_child_keyboard_delivered=wire.count(b'ready\r')==1,
                      post_child_UART_query_replied=b'\x1b[3;16R' in wire,
                      post_child_UART_input_rendered=screen[320:350:2]==b'AFTER-CWD-SETUP',
                      no_recovery_files=not any((folder/leaf).exists() for folder in (drive,drive/'OTHER') for leaf in ('PRMEDIT.BAK','PRMEDIT.$$$','PCPSTG.$$$','PCPBAK.$$$')))
        if mode=='startup':
            checks.update(no_CWD_child_requested=not (drive/'CWDMOVED.TXT').exists() and not (drive/'OTHER/WITNESS').exists())
        else:
            checks.update(actual_DOS_chdir_observed='before=D:\\\nafter=D:\\OTHER\n'==cwd,
                          child_created_witness_in_changed_directory=(drive/'OTHER/WITNESS').is_dir() and not (drive/'WITNESS').exists())
        report = dict(case=mode,passed=all(checks.values()),checks=checks,setup_child_record=setup,CWD_child_record=cwd,
                      result=str((drive/'result.json').relative_to(ROOT)),
                      artifacts={str(f.relative_to(drive)):sha(f) for f in drive.rglob('*') if f.is_file()})
        cases.append(report);(out/(mode+'.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(mode,{key:value for key,value in checks.items() if not value},flush=True)
        assert report['passed'],report
    inputs = ['standalone/test_cwd_identities_dos.py','standalone/cwd_identity_child.c',
              'standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py',
              'standalone/directory_test_support.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py']
    report = dict(passed=True,binary_sha256=sha(binary),cases=cases,original_inputs=[],
                  sources={name:sha(ROOT/name) for name in inputs},
                  child_sha256={leaf:sha(package/leaf) for leaf in ('CHDIR.EXE','PRMEDIT.EXE','DECOY.EXE')},
                  scope=__doc__+' Real DOSBox-X 8086 COM3/IRQ5, synthetic local serial modem, startup /S and original Alt-S/Alt-P dispatch, source-owned test-only setup child reads/copies PRM without editing it. Actual DOS chdir/getcwd/mkdir, live foreground return, late ANSI query/input and exact final UART/PIC/vector snapshots; startup, plain and directory-configured cases. Startup /S successfully returns before terminal dialing and proves absolute argv/sibling lookup, but it deliberately leaves PRM unchanged and does not cover editor-save/reload differences. No production editor UI, physical machine or Alt-F7 UI acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(cases),'actual DOS CWD identity cases')

if __name__ == '__main__':main()
