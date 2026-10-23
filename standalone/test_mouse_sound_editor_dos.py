#!/usr/bin/env python3
"""Actual combined editor navigation/save/discard with independent VGA sampling."""
import argparse,json,os,re,shutil,struct,subprocess
from pathlib import Path
from check_setup_model import image
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 import hashlib
 return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True);args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    out=ROOT/'build/setup-mouse-notice-sound'/args.label;out.mkdir(parents=True,exist_ok=False)
    base=ROOT/'build/setup-mouse-notice-sound';m=json.loads((base/'manifest.json').read_text());assert m['field_count']==51 and sha(base/'PRMEDIT.EXE')==m['binary_sha256']
    sources={**m['sources'],**{n:sha(ROOT/n) for n in ['standalone/test_mouse_sound_editor_dos.py','standalone/editor_view_probe.asm','standalone/check_setup_model.py','standalone/check_modem_import.py']}}
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    results=[]
    for name,initial,keys,want in [('save-on',0,'home del 1 f10 escape',1),('save-nonzero',1,'home del 6 5 5 3 5 f10 escape',65535),('discard',1,'home del 0 escape y',1),('invalid',0,'home del 6 5 5 3 6 f10 escape y',0)]:
        folder=out/name;folder.mkdir();shutil.copyfile(base/'PRMEDIT.EXE',folder/'PRMEDIT.EXE')
        before=bytearray(image());struct.pack_into('<HH',before,0x4e4,8,4);struct.pack_into('<H',before,0x1bc,initial);(folder/'VALID.PRM').write_bytes(before)
        expected=bytearray(before);struct.pack_into('<H',expected,0x1bc,want)
        subprocess.run(['nasm','-fbin',str(ROOT/'standalone/editor_view_probe.asm'),'-o',str(folder/'VIEW.COM')],check=True)
        sequence='pgdown '+'tab '*14+keys;schedule='ADDKEY p750 '+' p100 '.join(sequence.split())
        cfg=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{folder}"
c:
VIEW I
{schedule}
PRMEDIT VALID.PRM >LOG.TXT
if errorlevel 1 goto fail
VIEW
if errorlevel 1 goto fail
echo PASS>PASS.TXT
exit
:fail
echo FAIL>FAIL.TXT
exit
'''
        (folder/'dosbox.conf').write_text(cfg)
        with (folder/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],cwd=folder,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=25)
        raw=(folder/'VIEW.BIN').read_bytes() if (folder/'VIEW.BIN').exists() else b'';words=struct.unpack('<2H',raw[:4]) if len(raw)==4004 else ();chars=raw[4:][::2]
        checks=dict(emulator_exit=r.returncode==0,DOS_pass=(folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),whole_PRM_exact=(folder/'VALID.PRM').read_bytes()==bytes(expected),view_captured=bool(words) and words[0]==1,cursor_visible=bool(words) and words[1]>>8==18,
            last_field_visible=chars[18*80+2:18*80+15]==b'Program sound',help_not_overwritten=chars[19*80+2:19*80+10]==b'0 quiet;',viewport_scrolled=chars[5*80+2:5*80+10]==b'Autowrap',no_recovery_files=not (folder/'PRMEDIT.BAK').exists() and not (folder/'PRMEDIT.$$$').exists(),binary_unchanged=sha(folder/'PRMEDIT.EXE')==m['binary_sha256'])
        row=dict(passed=all(checks.values()),name=name,checks=checks,cursor=words[1] if words else None,captures_sha256={p.name:sha(p) for p in folder.iterdir() if p.is_file()})
        (folder/'result.json').write_text(json.dumps(row,indent=2)+'\n');results.append(row);print(name,'PASS' if row['passed'] else [n for n,v in checks.items() if not v],flush=True)
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    report=dict(passed=all(r['passed'] for r in results),cases=results,binary_sha256=m['binary_sha256'],sources=sources,scope=__doc__+' Ordinary51-field executable; no renamed main or product patch. The independent INT1C observer reads VGA/BDA only, then restores its vector. Synthetic settings, not private media or original PCSETUP.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
