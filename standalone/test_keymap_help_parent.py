#!/usr/bin/env python3
"""Connected DOS parent -> mapper embedded Help -> save -> live binding."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import subprocess
import test_connection_dos as lab
from modem_fixtures import fixture
from package_connection_test import terminal_companions,sha
from test_keymap_helper import image,changed

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('terminal','helper','output'):parser.add_argument('--'+name,required=True,type=Path)
    parser.add_argument('--trace-only',action='store_true',help='Small DOS EXEC trace without the larger VGA observer')
    parser.add_argument('--high-observer',action='store_true',help='Use386/UMB for the diagnostic VGA observer')
    parser.add_argument('--no-exec-trace',action='store_true',help='Use only the passive VGA observer')
    parser.add_argument('--expect-exec-memory-refusal',action='store_true',help='Diagnostic external-process placement must fail with real DOS8')
    args=parser.parse_args();parent=args.terminal.resolve();helper=args.helper.resolve();out=args.output.resolve()
    assert parent.is_relative_to(ROOT/'build') and helper.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads(parent.with_name('manifest.json').read_text());proof=json.loads(helper.with_name('result.json').read_text())
    assert manifest['experimental_keymap_editor'] and sha(parent)==manifest['binary_sha256']
    assert proof['passed'] and proof['original_inputs']==[] and sha(helper)==proof['binary_sha256']
    assert bool(proof.get('diagnostic_build'))==args.expect_exec_memory_refusal
    assert not args.expect_exec_memory_refusal or not args.no_exec_trace
    for name,digest in {**manifest['sources'],**proof['sources']}.items():assert sha(ROOT/name)==digest,name
    companions,sources=terminal_companions(parent,manifest);out.mkdir(parents=True);runtime=out/'runtime';runtime.mkdir()
    for name,path in {'TERMINAL.EXE':parent,'PCKEYMAP.EXE':helper,**companions}.items():shutil.copyfile(path,runtime/name)
    products={p.name:sha(p) for p in runtime.iterdir()};lab.BINARY=runtime/'TERMINAL.EXE'
    watch=(ROOT/'standalone/path_dialog_watch.asm').read_text();begin=watch.index(' cmp word [es:806]');end=watch.index('%if WATCH_KIND',begin)
    watch=watch[:begin]+" cmp word [es:2],0x714b\n jne .done\n cmp word [es:4],0x7165\n jne .done\n cmp word [es:6],0x7179\n jne .done\n cmp byte [es:10],'M'\n jne .done\n"+watch[end:]
    watch=watch.replace('D:\\PATHVIEW.BIN','D:\\HELPVIEW.BIN');(out/'watch.asm').write_text(watch)
    subprocess.run(['nasm','-fbin','-DWATCH_KIND=0',str(out/'watch.asm'),'-o',str(out/'WATCH.COM')],check=True)
    subprocess.run(['nasm','-fbin',str(ROOT/'standalone/help_exec_watch.asm'),'-o',str(out/'EXCWATCH.COM')],check=True)
    settings=bytearray(fixture())
    for at,value in ((0x4e4,8),(0x4e6,4),(0x194,6),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x3e4,7),(0x3e6,11),(0x3e8,113)):
        struct.pack_into('<H',settings,at,value)
    rows=[]
    for count in (7,33):
        label=out.name+'-'+str(count);drive=ROOT/'build/connection-dos'/label;assert not drive.exists()
        initial=image()[:count*948]
        keys='p900 enter p3000 a-f8 p1600 f1 p100 tab n e w enter p200 a-z p1400 escape p300 a-s p500 escape p1000 f1 p250 r e a d y p500 a-x'
        r=lab.run(label,'success',keys,prm=bytes(settings),arguments='@D:\\TEST.PRM /D:CaseTest:23 /K:D:\\SYN.KBD COM1 19200 HARD',
            files={'SYN.KBD':initial,'WATCH.COM':(out/'WATCH.COM').read_bytes(),'EXCWATCH.COM':(out/'EXCWATCH.COM').read_bytes()},
            cpu='386' if args.high_observer else '8086',working_drive='d',observer=None if args.trace_only else 'WATCH',
            observer_high=args.high_observer,auxiliary=() if args.no_exec_trace else ('EXCWATCH',),timeout=35)
        checks=dict(r['checks']);checks.pop('fixture_unchanged_SYN.KBD');wire=(drive/'serial.bin').read_bytes()
        if not args.trace_only:
            raw=(drive/'HELPVIEW.BIN').read_bytes();magic,flags,ticks=struct.unpack_from('<3H',raw)
            checks['correct_context_observed']=magic==0x5044 and ticks>0 and ((flags==2) if args.expect_exec_memory_refusal else (flags==3 and b'A keyboard profile' in raw[6:4006:2]))
        events=[]
        if not args.no_exec_trace:
            trace=(drive/'EXECTRAC.BIN').read_bytes();magic,event_count,unhook=struct.unpack_from('<3H',trace)
            events=[dict(zip(('function','result','flags'),struct.unpack_from('<3H',trace,6+i*24)),path=trace[12+i*24:30+i*24].split(b'\0')[0].decode('ascii')) for i in range(event_count)]
            nested=[i for i,event in enumerate(events) if event['function']==0x4b00 and event['path'].upper().endswith('PCHELP.RTE')]
            checks['trace_vector_restored']=magic==0x4b48 and unhook==1
            if args.expect_exec_memory_refusal:checks['actual_DOS8_Help_refusal']=len(nested)==1 and events[nested[0]]['flags']&1 and events[nested[0]]['result']==8
            else:checks['no_extra_Help_EXEC']=not nested
        checks.update(exact_KBD=(drive/'SYN.KBD').read_bytes()==changed(initial),live_binding_resumed=b'newready' in wire,
            products_unchanged=all(sha(runtime/name)==digest for name,digest in products.items()))
        row=dict(profiles=count,passed=all(checks.values()),checks=checks,exec_events=events,raw_result=str((drive/'result.json').relative_to(ROOT)))
        (out/(str(count)+'.json')).write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
        assert row['passed'],(count,[name for name,value in checks.items() if not value]);print('PASS parent mapper Help:',count,flush=True)
    names=['standalone/test_keymap_help_parent.py','standalone/help_exec_watch.asm','standalone/test_connection_dos.py','standalone/modem_fixtures.py','standalone/test_keymap_helper.py','standalone/package_connection_test.py','standalone/path_dialog_watch.asm']
    result=dict(passed=True,parent_sha256=sha(parent),helper_sha256=sha(helper),products=products,cases=rows,cpu='386' if args.high_observer else '8086',VGA_observer_high=args.high_observer,trace_only=args.trace_only,exec_trace=not args.no_exec_trace,expected_DOS8=args.expect_exec_memory_refusal,original_inputs=[],
        sources={**sources,**{name:sha(ROOT/name) for name in names}},scope=__doc__+' Real DOS/BIOS/files/UART and full embedded source Help; optional passive VGA observer plus real DOS EXEC trace. Synthetic modem, no physical/private-machine acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
