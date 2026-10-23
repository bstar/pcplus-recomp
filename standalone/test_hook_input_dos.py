#!/usr/bin/env python3
"""Actual helper/profile/XLT staging with frozen paths and hostile CWD decoys."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
from check_setup_model import image
from test_terminal import SAMPLER

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def keymap(profile):
    return b''.join(bytes([65+(profile+i)%26,0])+bytes([(profile*13+i)&255])*10 for i in range(79))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-inputprobe'
    manifest=json.loads((base/'manifest.json').read_text());assert manifest['hook_input_probe'] and manifest['experimental_hook_input']
    assert sha(base/'TERMINAL.EXE')==manifest['binary_sha256']
    def compile(folder):
        subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
                        '-fm=INPUTCH.map','-fe=INPUTCH.EXE',str(ROOT/'standalone/hook_input_child.c'),
                        str(base/'hook_exchange.obj')],cwd=folder,check=True)
    compile(out)
    table=bytes((i*73+19)&255 for i in range(256));fallback=bytes((i*11+201)&255 for i in range(256))
    explicit=bytes((i*17+42)&255 for i in range(256));decoy=bytes((i*7+3)&255 for i in range(256))
    keyboard=b''.join(keymap(p) for p in range(7))
    recipes=[
        dict(name='unchanged-no-files',profile=4,mode=0),
        dict(name='default-profile-six',profile=6,mode=0),
        dict(name='import-four-to-six',profile=6,mode=1,kbd=True,xlt=table),
        dict(name='import-six-to-four',initial_profile=6,profile=4,mode=1,kbd=True,xlt=table),
        dict(name='changed-keyboard-removed',profile=6,mode=1,kbd=True,xlt=table,remove_kbd=True,status=4),
        dict(name='new-keyboard-block-bad',profile=6,mode=1,kbd=True,bad_slot=True,xlt=table,status=4),
        dict(name='new-keyboard-block-absent',profile=6,mode=0,kbd=True,short_kbd=True,status=4),
        dict(name='xlt-current-short',profile=6,mode=1,kbd=True,xlt=table[:255],status=5),
        dict(name='xlt-current-long',profile=6,mode=1,kbd=True,xlt=table+b'X',status=5),
        dict(name='xlt-current-missing',profile=4,mode=1,status=5),
        dict(name='xlt-fallback-valid',profile=6,mode=1,kbd=True,fallback=fallback),
        dict(name='xlt-current-bad-no-fallback',profile=6,mode=1,kbd=True,xlt=table[:255],fallback=fallback,status=5),
        dict(name='xlt-fallback-bad',profile=4,mode=1,fallback=fallback[:255],status=5),
        dict(name='mode-two-no-file',profile=6,mode=2,kbd=True),
        dict(name='mode-two-to-zero',profile=4,mode=0,initial_mode=2),
        dict(name='unchanged-one-removed-file',profile=4,mode=1,initial_mode=1,xlt=table,remove_xlt=True),
        dict(name='explicit-xlt-fixed-mode',profile=4,mode=0,explicit=True,status=3),
        dict(name='explicit-xlt-unchanged',profile=4,mode=1,explicit=True),
        dict(name='unchanged-keyboard-removed',profile=4,mode=0,kbd=True,remove_kbd=True),
    ]
    cases=[]
    for recipe in recipes:
        name=recipe['name'];folder=out/name;folder.mkdir();(folder/'ALT').mkdir();(folder/'LIB').mkdir()
        raw=bytearray(image());initial_profile=recipe.get('initial_profile',4);initial_mode=recipe.get('initial_mode',0)
        struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<H',raw,0x194,initial_profile)
        struct.pack_into('<H',raw,0x1e0,initial_mode);(folder/'TEST.PRM').write_bytes(raw)
        if recipe.get('kbd'):
            kbd=bytearray(keyboard)
            if recipe.get('bad_slot'):kbd[6*948:6*948+12]=b'X'*12
            if recipe.get('short_kbd'):kbd=kbd[:5*948]
            (folder/'KEYS.KBD').write_bytes(kbd)
        if 'xlt' in recipe:(folder/'PCPLUS.XLT').write_bytes(recipe['xlt'])
        if 'fallback' in recipe:(folder/'LIB/PCPLUS.XLT').write_bytes(recipe['fallback'])
        if recipe.get('explicit'):(folder/'LOCK.XLT').write_bytes(explicit)
        (folder/'ALT/PCPLUS.XLT').write_bytes(decoy)
        (folder/'ALT/KEYS.KBD').write_bytes(b''.join(keymap((p+3)%7)for p in range(7)))
        context=recipe['profile']|(recipe['mode']<<4)|256|(512 if recipe.get('remove_kbd') else 0)|(1024 if recipe.get('remove_xlt') else 0)
        expected=recipe.get('status',0)
        (folder/'CASE.BIN').write_bytes(struct.pack('<3H',context,expected,3 if expected else 4))
        shutil.copyfile(base/'TERMINAL.EXE',folder/'TERMINAL.EXE');shutil.copyfile(out/'INPUTCH.EXE',folder/'INPUTCH.EXE')
        (folder/'sampler.asm').write_text(SAMPLER)
        subprocess.run(['nasm','-fbin',str(folder/'sampler.asm'),'-o',str(folder/'SNAP.COM')],check=True)
        options='@TEST.PRM /I:3'+(' /K:KEYS.KBD' if recipe.get('kbd') else '')+(' /X:LOCK.XLT' if recipe.get('explicit') else '')
        fallback_path=r'D:\LIB' if 'fallback' in recipe else ''
        (folder/'dosbox.conf').write_text(fr'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount d "{folder}"
d:
set PCPLUS={fallback_path}
SNAP B
TERMINAL {options}
if errorlevel 1 goto fail
echo PASS>D:\PASS.TXT
goto done
:fail
echo FAIL>D:\FAIL.TXT
:done
cd D:\
D:\SNAP.COM A
exit
''')
        with (folder/'dosbox.log').open('w') as log:
            run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],cwd=folder,
                               env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
        assert run.returncode==0 and (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),name
        assert (folder/'TEST.PRM').read_bytes()==raw
        assert (folder/'BASE0.BIN').read_bytes()==(folder/'BASE1.BIN').read_bytes()
        assert (folder/'BASE0.BIN').read_bytes()[8:]==raw
        assert (folder/'PBEFORE.BIN').read_bytes()==(folder/'PAFTER.BIN').read_bytes()
        assert (folder/'KEY0.BIN').read_bytes()==(folder/'KEY1.BIN').read_bytes()
        assert (folder/'TABLE0.BIN').read_bytes()==(folder/'TABLE1.BIN').read_bytes()
        assert (folder/'LIVE0.BIN').read_bytes()==(folder/'LIVE1.BIN').read_bytes()
        assert (folder/'EDIT0.BIN').read_bytes()==(folder/'EDIT1.BIN').read_bytes()
        assert (folder/'CWD.BIN').read_bytes()==b'ALT\0'.ljust(64,b'\0')
        assert (folder/'BANK0.BIN').read_bytes()==(folder/'BANK1.BIN').read_bytes()==bytes(830)
        assert (folder/'STACK.BIN').read_bytes()==b'\xa5'*256
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
        assert len((folder/'BEFORE.BIN').read_bytes())==42
        result=struct.unpack('<6H',(folder/'RESULTS.BIN').read_bytes());assert result[0]==expected
        offer=(folder/'OFFER.BIN').read_bytes();assert len(offer)==1212
        current_mode=1 if recipe.get('explicit') else initial_mode
        current_keys=keymap(initial_profile) if recipe.get('kbd') else (folder/'KEY0.BIN').read_bytes()
        assert (folder/'KEY0.BIN').read_bytes()==current_keys
        current_table=explicit if recipe.get('explicit') else table if initial_mode==1 else bytes(256)
        assert (folder/'TABLE0.BIN').read_bytes()==current_table
        if expected:assert offer==b'X'*1212
        else:
            changed_profile=recipe['profile']!=initial_profile;changed_mode=recipe['mode']!=current_mode
            header=struct.pack('<4H',recipe['profile'],recipe['mode'],int(changed_profile),int(changed_mode))
            wanted_keys=keymap(recipe['profile']) if changed_profile and recipe.get('kbd') else current_keys
            wanted_table=(recipe.get('xlt',recipe.get('fallback')) if changed_mode and recipe['mode']==1 else current_table)
            assert offer==header+wanted_keys+wanted_table,name
        proposal=(folder/'PROPOSAL.BIN').read_bytes();projected=bytearray((folder/'PBEFORE.BIN').read_bytes())
        struct.pack_into('<H',projected,0x194,recipe['profile']);struct.pack_into('<H',projected,0x1e0,recipe['mode'])
        assert proposal[830:2094]==projected
        assert proposal[:20]==b'\x3c'+bytes(19) and proposal[20:23]==b'KB\0'
        assert sha(folder/'TERMINAL.EXE')==manifest['binary_sha256']
        cases.append(dict(case=name,passed=True,status=expected,recipe=recipe|{k:v.hex() for k,v in recipe.items() if isinstance(v,bytes)},
                          artifacts={str(p.relative_to(folder)):sha(p)for p in folder.rglob('*')if p.is_file()}))
        print('PASS8086',name,'status',expected,flush=True)
    rebuild=out/'rebuild';rebuild.mkdir();compile(rebuild)
    assert sha(rebuild/'INPUTCH.EXE')==sha(out/'INPUTCH.EXE')
    sources=dict(manifest['sources'])
    for name in ['standalone/test_hook_input_dos.py','standalone/hook_input_child.c','standalone/check_setup_model.py',
                 'standalone/check_modem_import.py','standalone/test_terminal.py']:sources[name]=sha(ROOT/name)
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    report=dict(passed=True,cases=cases,sources=sources,binary_sha256=manifest['binary_sha256'],helper_sha256=sha(out/'INPUTCH.EXE'),
                original_inputs=[],scope='Actual8086 terminal startup/helper EXEC/modem+input preparation. Frozen keyboard/XLT paths '
                'with helper CWD mutation and valid decoys; whole offers, file rejection, unchanged active keys/table/mode/PRM/registers/baseline/hardware. '
                'Diagnostic before UART/mouse acquisition. No input-resource adoption, interactive helper routing or physical acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(cases),'DOS input resource workflows')


if __name__=='__main__':main()
