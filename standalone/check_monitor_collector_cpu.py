#!/usr/bin/env python3
"""Prove observer collector branch encodings and their8086-mode correction."""
import argparse,json,os,shutil,subprocess
from pathlib import Path
import test_terminal_monitor_dos as monitor
from audit_aspect_transmit_wait import ROOT,sha

PROBE='''bits 16
CPU 8086
org 100h
mov ax,0xb800
mov es,ax
xor di,di
mov cx,2000
mov ax,0x0758
cld
rep stosw
xor ah,ah
int 0x16
cmp al,'2'
jne fail
mov ax,0x4c00
int 0x21
fail:
mov ax,0x4c01
int 0x21
'''


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    inputs={str(path.relative_to(ROOT)):sha(path) for path in (Path(__file__),Path(monitor.__file__),ROOT/'standalone/test_terminal_capture_dos.py',ROOT/'standalone/test_terminal_transfer_dos.py',ROOT/'nix/flake.lock')}
    for name,digest in inputs.items():
        dest=out/'inputs'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest);assert sha(dest)==digest
    collector=monitor.OBSERVER_DUMP.replace('org 100h','org 100h\n pushf\n pop ax\n mov [entry_flags],ax\n cld')
    collector=collector.replace('mov cx,4034','mov cx,4036').replace('cmp ax,4034','cmp ax,4036')+'\nentry_flags dw 0\n'
    rows=[]
    for variant,cpu in ((variant,cpu) for variant in ('legacy','fixed') for cpu in ('386','8086')):
        folder=out/(variant+'-'+cpu);folder.mkdir()
        for name,text in [('MONOBS',monitor.OBSERVER),('MONDUMP',collector),('PROBE',PROBE)]:
            if variant=='legacy' and name!='PROBE':text=text.replace('CPU 8086\n','')
            else:assert 'CPU 8086' in text
            source=folder/(name+'.asm');source.write_text(text);subprocess.run(['nasm','-fbin',str(source),'-o',str(folder/(name+'.COM'))],check=True)
        config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype={cpu}
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{folder}"
c:
MONOBS
if errorlevel 1 goto fail
ADDKEY p500 2
PROBE
if errorlevel 1 goto fail
MONDUMP
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto finished
:fail
echo FAIL>FAIL.TXT
:finished
exit
''';(folder/'dosbox.conf').write_text(config)
        with (folder/'dosbox.log').open('w') as log:
            try:status=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=10).returncode
            except subprocess.TimeoutExpired:status=-1
        dump=(folder/'MONVIEW.BIN').read_bytes() if (folder/'MONVIEW.BIN').exists() else b''
        accepted=status==0 and (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists() and len(dump)==4036 and dump[:14]==b'MV16\x0f\x00\x3a\xc5\x01\x00\x01\x00\x00\x00'
        rows.append(dict(assembler_variant=variant,CPU_mode=cpu,exit_code=status,collector_accepted=accepted,report_bytes=len(dump),artifacts={path.name:sha(path) for path in folder.iterdir() if path.is_file()}))
        print(json.dumps({k:rows[-1][k] for k in ('assembler_variant','CPU_mode','exit_code','collector_accepted','report_bytes')}),flush=True)
    assert [r['collector_accepted'] for r in rows]==[True,False,True,True] and rows[1]['exit_code']==-1
    for variant in ('legacy','fixed'):
        for name in ('MONOBS.COM','MONDUMP.COM','PROBE.COM'):assert sha(out/(variant+'-386')/name)==sha(out/(variant+'-8086')/name)
    legacy=(out/'legacy-8086/MONDUMP.COM').read_bytes();fixed=(out/'fixed-8086/MONDUMP.COM').read_bytes()
    assert legacy[17:19]==bytes.fromhex('0f85') and fixed[17:20]==bytes.fromhex('7403e9')
    result=dict(passed=True,helper_encoding_gap_reproduced=True,collector_8086_accepted=True,cases=rows,inputs=inputs,checker_sha256=sha(Path(__file__)),
        branch_encoding=dict(file_offset=17,legacy=legacy[17:21].hex(),fixed=fixed[17:22].hex()),
        scope=__doc__+' Source-only TSR, BIOS/video probe and collector; no PCPlus binary is loaded. Legacy strips CPU8086 directives deliberately to reproduce default-NASM386 near Jcc emission; fixed helpers require CPU8086 and use inverse short Jcc plus near JMP. Identical binaries within each variant run in386/8086 mode. Only legacy8086 times out; both fixed modes restore vectors and write the report. This corrects the test helper, not application code, and is not physical hardware acceptance.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
