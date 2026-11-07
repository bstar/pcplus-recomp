#!/usr/bin/env python3
"""Source mapper new-file workflow; explicit save only, no invented mappings."""
import argparse
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
from test_keymap_helper import image,changed,sha

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();build=args.build.resolve();out=args.output.resolve()
    assert build.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads((build/'result.json').read_text())
    assert manifest['passed'] and manifest['original_inputs']==[] and sha(build/'PCKEYMAP.EXE')==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    tree=ast.parse((ROOT/'standalone/test_meta_dialog_vga.py').read_text())
    sampler=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='sampler' for t in n.targets))
    out.mkdir(parents=True);short=image()[:7*948];blank=bytes(31284);edit='f1 p60 tab n e w enter p120 '
    cases=[
        ('missing-exit',False,6,'escape',{},0),
        ('missing-save-blank',False,6,'a-s p350 escape',{'NEW.KBD':blank},0),
        ('missing-save',False,6,edit+'a-s p350 escape',{'NEW.KBD':changed(blank)},0),
        ('missing-discard',False,6,edit+'escape p100 n',{},0),
        ('missing-save-on-exit',False,6,edit+'escape p100 y',{'NEW.KBD':changed(blank)},0),
        ('missing-profile32',False,32,edit+'a-s p350 escape',{'NEW.KBD':changed(blank,32)},0),
        ('open-new-unsaved',True,6,'a-o p100 n e w enter p300 escape',{},0),
        ('open-new-save',True,6,'a-o p100 n e w enter p300 '+edit+'a-s p350 escape',{'NEW.KBD':changed(blank)},0),
        ('discard-existing-open-new',True,6,edit+'a-o p100 n p100 n e w enter p300 '+edit+'a-s p350 escape',{'NEW.KBD':changed(blank)},0),
        ('new-open-existing',False,6,'a-o p100 o l d enter p300 '+edit+'a-s p350 escape',{'OLD.KBD':changed(short)},0),
        ('new-dirty-open-existing',False,6,edit+'a-o p100 n p100 o l d enter p300 '+edit+'a-s p350 escape',{'OLD.KBD':changed(short)},0),
        ('new-repeat-save',False,6,edit+'a-s p350 f2 p60 tab n e w enter p120 a-s p350 escape',{'NEW.KBD':changed(changed(blank),6,17)},0),
        ('new-stage-conflict',False,6,edit+'a-s p150 space p120 escape p100 n',{},0),
        ('missing-parent',False,6,'',{},3),
        ('empty-existing',False,6,'',{'NEW.KBD':b''},3),
    ];rows=[]
    for name,existing,profile,keys,changes,status in cases:
        folder=out/name;folder.mkdir();shutil.copyfile(build/'PCKEYMAP.EXE',folder/'PCKEYMAP.EXE');(folder/'OLD.KBD').write_bytes(short)
        if name=='empty-existing':(folder/'NEW.KBD').write_bytes(b'')
        if name=='new-stage-conflict':(folder/'KBDSTG.$$$').write_bytes(b'OWNED RECOVERY')
        for leaf in ('BEFORE','AFTER'):
            asm=folder/(leaf+'.ASM');asm.write_text(sampler.replace('BEFORE.BIN',leaf+'.BIN'))
            subprocess.run(['nasm','-fbin',str(asm),'-o',str(folder/(leaf+'.COM'))],check=True)
        target='ABSENT\\NEW.KBD' if name=='missing-parent' else 'OLD.KBD' if existing else 'NEW.KBD'
        branch='if errorlevel 4 goto failed\nif errorlevel 3 goto captured\ngoto failed\n' if status else 'if errorlevel 1 goto failed\ngoto captured\n'
        (folder/'CHECK.BAT').write_text('@echo off\ncls\nBEFORE\nADDKEY p700 '+keys+'\nPCKEYMAP '+str(profile)+' '+target+' >CMD.LOG\n'+branch+':captured\nAFTER\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
        (folder/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "'+str(folder)+'"\nc:\nCHECK.BAT\n')
        with (folder/'dosbox.log').open('w') as log:
            subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=20)
        assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),name
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes(),(name,'screen/cursor/shape')
        expected={'OLD.KBD':short,**changes}
        assert {p.name:p.read_bytes() for p in folder.glob('*.KBD')}==expected,name
        assert not (folder/'KBDBAK.$$$').exists(),name
        if name=='new-stage-conflict':assert (folder/'KBDSTG.$$$').read_bytes()==b'OWNED RECOVERY'
        else:assert not (folder/'KBDSTG.$$$').exists(),name
        assert sha(folder/'PCKEYMAP.EXE')==manifest['binary_sha256']
        rows.append(dict(case=name,passed=True,exit=status,file_bytes={leaf:len(data) for leaf,data in expected.items()},exact_files_and_screen=True))
        print('PASS source new file:',name,flush=True)
    names=['standalone/test_keymap_newfile.py','standalone/test_keymap_helper.py','standalone/test_meta_dialog_vga.py']
    result=dict(passed=True,helper_sha256=manifest['binary_sha256'],cases=rows,cpu='8086',original_inputs=[],sources={name:sha(ROOT/name) for name in names},
        scope=__doc__+' Exact files/lengths and screen/cursor/shape on owned media. Missing leaf starts blank33 profiles; creation only on explicit save. Does not cover parent/connected BBS or physical filesystem failure.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
