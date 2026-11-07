#!/usr/bin/env python3
"""Foreground short-KBD workflows, cross-length Open and exact byte preservation."""
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
    out.mkdir(parents=True)
    tree=ast.parse((ROOT/'standalone/test_meta_dialog_vga.py').read_text())
    sampler=next(ast.literal_eval(node.value) for node in ast.walk(tree) if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='sampler' for target in node.targets))
    full=image();short=full[:7*948];one=full[:948];edit='f1 p60 tab n e w enter p120 '
    malformed=bytearray(short);malformed[6*948+16*12:6*948+17*12]=b'BADBADBADBAD'
    cases=[
        ('short-save',short,6,edit+'a-s p350 escape','SYN.KBD',6,0),
        ('one-save',one,0,edit+'a-s p350 escape','SYN.KBD',0,0),
        ('next-wrap',short,6,'space p100 '+edit+'a-s p350 escape','SYN.KBD',0,0),
        ('previous-wrap',short,0,'pgup p100 '+edit+'a-s p350 escape','SYN.KBD',6,0),
        ('open-short-clamp',full,32,'a-o p100 s h o r t enter p300 '+edit+'a-s p350 escape','SHORT.KBD',0,0),
        ('open-one-clamp',short,6,'a-o p100 o n e enter p300 '+edit+'a-s p350 escape','ONE.KBD',0,0),
        ('open-full-preserve',short,6,'a-o p100 f u l l enter p300 '+edit+'a-s p350 escape','FULL.KBD',6,0),
        ('open-short-preserve',full,3,'a-o p100 s h o r t enter p300 '+edit+'a-s p350 escape','SHORT.KBD',3,0),
        ('failed-open-keeps-count',full,32,'a-o p100 s h o r t enter p300 space p100 space p100 '+edit+'a-s p350 escape','SYN.KBD',0,0),
        ('discard-missing',short,6,edit+'a-o p100 n p100 m i s s i n g enter p300 space p120 escape',None,None,0),
        ('readonly',short,6,edit+'a-s p150 space p120 escape p100 n',None,None,0),
        ('conflict',short,6,edit+'a-s p150 space p120 escape p100 n',None,None,0),
        ('legacy',short,6,edit+'a-s p350 escape','SYN.KBD',6,0),
        ('missing-profile',short,7,'',None,None,3),
        ('truncated',short[:-1],6,'',None,None,3),
        ('empty',b'',0,'',None,None,3),
        ('oversized',full+b'X',6,'',None,None,3),
        ('malformed',bytes(malformed),6,'',None,None,3),
        ('absent',None,6,'escape',None,None,0),
    ]
    rows=[]
    for name,initial,profile,keys,edited,edited_profile,status in cases:
        folder=out/name;folder.mkdir();shutil.copyfile(build/'PCKEYMAP.EXE',folder/'PCKEYMAP.EXE')
        files={'SHORT.KBD':bytes(malformed) if name=='failed-open-keeps-count' else short,'FULL.KBD':full,'ONE.KBD':one}
        if initial is not None:files['SYN.KBD']=initial
        for leaf,raw in files.items():(folder/leaf).write_bytes(raw)
        if name=='conflict':(folder/'KBDSTG.$$$').write_bytes(b'OWNED CONFLICT')
        for leaf in ('BEFORE','AFTER'):
            asm=folder/(leaf+'.ASM');asm.write_text(sampler.replace('BEFORE.BIN',leaf+'.BIN'))
            subprocess.run(['nasm','-fbin',str(asm),'-o',str(folder/(leaf+'.COM'))],check=True)
        branch=('if errorlevel 4 goto failed\nif errorlevel 3 goto captured\ngoto failed\n' if status else 'if errorlevel 1 goto failed\ngoto captured\n')
        batch='@echo off\n'+('attrib +r SYN.KBD\n' if name=='readonly' else '')+'cls\nBEFORE\nADDKEY p700 '+keys+'\nPCKEYMAP '+str(profile)+' SYN.KBD'+(' /LEGACY' if name in ('legacy','previous-wrap') else '')+' >CMD.LOG\n'+branch+':captured\nAFTER\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n'
        (folder/'CHECK.BAT').write_text(batch)
        (folder/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(folder)+'"\nc:\nCHECK.BAT\n')
        with (folder/'dosbox.log').open('w') as log:
            subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=20)
        assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),name
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes(),(name,'screen/cursor/shape')
        expected=dict(files)
        if edited:expected[edited]=changed(expected[edited],edited_profile)
        for leaf,raw in expected.items():assert (folder/leaf).read_bytes()==raw,(name,leaf)
        if initial is None:assert not (folder/'SYN.KBD').exists()
        assert not (folder/'MISSING.KBD').exists() and not (folder/'KBDBAK.$$$').exists()
        if name=='conflict':assert (folder/'KBDSTG.$$$').read_bytes()==b'OWNED CONFLICT'
        else:assert not (folder/'KBDSTG.$$$').exists()
        assert sha(folder/'PCKEYMAP.EXE')==manifest['binary_sha256']
        rows.append(dict(case=name,passed=True,exit=status,file_bytes={leaf:len(raw) for leaf,raw in expected.items()},all_bytes_and_screen_preserved=True))
        print('PASS prefix helper',name,flush=True)
    names=['standalone/test_keymap_prefix_helper.py','standalone/test_keymap_helper.py','standalone/test_meta_dialog_vga.py']
    result=dict(passed=True,helper_sha256=manifest['binary_sha256'],cases=rows,cpu='8086',original_inputs=[],
                sources={name:sha(ROOT/name) for name in names},scope='Owned short1/7/full33 foreground navigation/save/Open/clamp/failure workflows and rejected initial files. Every file byte/length plus screen/cursor/shape required; no parent or physical acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
