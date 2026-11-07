#!/usr/bin/env python3
"""Real source mapper embedded Help context17, bindings and VGA restoration."""
import argparse
import ast
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
from test_keymap_helper import image,changed,sha

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('build','help-build','output'):parser.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args();build=args.build.resolve();help_build=args.help_build.resolve();out=args.output.resolve()
    assert build.is_relative_to(ROOT/'build') and help_build.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads((build/'result.json').read_text());bundle=json.loads((help_build/'package.json').read_text())
    assert manifest['passed'] and manifest['original_inputs']==[] and sha(build/'PCKEYMAP.EXE')==manifest['binary_sha256']
    for record in (manifest,bundle):
        for name,digest in record['sources'].items():assert sha(ROOT/name)==digest,name
    for name in ('PCHELP.RTE','PCPLUS.HLP'):assert sha(help_build/name)==bundle['products'][name]
    tree=ast.parse((ROOT/'standalone/test_meta_dialog_vga.py').read_text())
    sampler=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='sampler' for t in n.targets))
    watch=(ROOT/'standalone/path_dialog_watch.asm').read_text();begin=watch.index(' cmp word [es:806]');end=watch.index('%if WATCH_KIND',begin)
    watch=watch[:begin]+" cmp word [es:2],0x714b\n jne .done\n cmp word [es:4],0x7165\n jne .done\n cmp word [es:6],0x7179\n jne .done\n cmp byte [es:10],'M'\n jne .done\n"+watch[end:]
    watch=watch.replace('D:\\PATHVIEW.BIN','C:\\HELPVIEW.BIN')
    out.mkdir(parents=True);rows=[];edit='f1 p100 tab n e w enter p150 '
    cases=[('full-clean',33,'a-z p1200 escape p300 escape',False),
           ('full-dirty',33,edit+'a-z p1200 escape p300 a-s p350 escape',True),
           ('short-dirty',7,edit+'a-z p1200 escape p300 a-s p350 escape',True),
           ('repeat',7,edit+'a-z p1200 escape p300 a-z p700 escape p300 a-s p350 escape',True),
           ('missing-program',7,edit+'a-z p1200 escape p300 a-s p350 escape',True),
           ('missing-resource',7,edit+'a-z p300 space p250 a-s p350 escape',True),
           ('bad-resource',7,edit+'a-z p300 space p250 a-s p350 escape',True),
           ('topics',7,edit+'a-z p500 t p500 escape p250 escape p300 a-s p350 escape',True),
           ('search',7,edit+'a-z p500 s p500 p r o f i l e enter p250 escape p300 a-s p350 escape',True)]
    for name,count,keys,edited in cases:
        folder=out/name;folder.mkdir();initial=image()[:count*948];(folder/'SYN.KBD').write_bytes(initial)
        shutil.copyfile(build/'PCKEYMAP.EXE',folder/'PCKEYMAP.EXE')
        if name!='missing-program':shutil.copyfile(help_build/'PCHELP.RTE',folder/'PCHELP.RTE')
        if name!='missing-resource':(folder/'PCPLUS.HLP').write_bytes(b'INVALID' if name=='bad-resource' else (help_build/'PCPLUS.HLP').read_bytes())
        for leaf in ('BEFORE','AFTER'):
            asm=folder/(leaf+'.ASM');asm.write_text(sampler.replace('BEFORE.BIN',leaf+'.BIN'))
            subprocess.run(['nasm','-fbin',str(asm),'-o',str(folder/(leaf+'.COM'))],check=True)
        observed_watch=watch
        if name=='topics':observed_watch=watch.replace(" cmp word [es:2],0x714b", " cmp byte [es:1004],201\n jne .done\n cmp word [es:2],0x714b")
        if name=='search':observed_watch=watch.replace(" cmp word [es:2],0x714b", " cmp word [es:1784],0x7145\n jne .done\n cmp word [es:2],0x714b")
        (folder/'WATCH.ASM').write_text(observed_watch);subprocess.run(['nasm','-fbin','-DWATCH_KIND=0',str(folder/'WATCH.ASM'),'-o',str(folder/'WATCH.COM')],check=True)
        (folder/'CHECK.BAT').write_text('@echo off\ncls\nBEFORE\nWATCH T\nADDKEY p700 '+keys+'\nPCKEYMAP 6 SYN.KBD\nif errorlevel 1 goto failed\nAFTER\nWATCH\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
        (folder/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "'+str(folder)+'"\nc:\nCHECK.BAT\n')
        with (folder/'dosbox.log').open('w') as log:
            subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=25)
        assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),name
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes(),(name,'screen/cursor/shape')
        assert (folder/'SYN.KBD').read_bytes()==(changed(initial) if edited else initial),name
        raw=(folder/'HELPVIEW.BIN').read_bytes();magic,flags,ticks=struct.unpack_from('<3H',raw)
        expected_help=name not in ('missing-resource','bad-resource')
        assert magic==0x5044 and bool(flags&1)==expected_help and flags&2 and ticks,name
        if expected_help:assert (b'Enter help text' if name=='search' else b'A keyboard profile') in raw[6:4006:2],name
        assert not (folder/'KBDSTG.$$$').exists() and not (folder/'KBDBAK.$$$').exists()
        assert sha(folder/'PCKEYMAP.EXE')==manifest['binary_sha256']
        rows.append(dict(case=name,passed=True,profiles=count,help_observed=expected_help,exact_KBD_and_outer_frame=True,observer_unhook_verified=True))
        print('PASS mapper Help:',name,flush=True)
    names=['standalone/test_keymap_help.py','standalone/test_keymap_helper.py','standalone/test_meta_dialog_vga.py','standalone/path_dialog_watch.asm']
    result=dict(passed=True,helper_sha256=manifest['binary_sha256'],help_products={name:bundle['products'][name] for name in ('PCHELP.RTE','PCPLUS.HLP')},cases=rows,cpu='8086',original_inputs=[],sources={name:sha(ROOT/name) for name in names},
        scope=__doc__+' Same full source Help viewer compiled into mapper, passive VGA timer and owned synthetic KBD. Topics/search are captured. Missing/bad HLP returns without losing edits; RTE is unnecessary here. No terminal-parent/BBS/physical or exact intermediate editor-frame acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
