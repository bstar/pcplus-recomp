#!/usr/bin/env python3
"""Actual DOS ASIOv2 receive policy and raw parent handback checks.

Authored expectations are independent of production execution. Parent handback
passes through the actual recovered UART dequeue and maintained terminal mapper;
unused terminal startup/display services are explicit interrupt traps.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time
from test_aspect_script_serial_dos import ROOT, sha

sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source

ADAPTER = r'''
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_translation_table,terminal_translation_enabled,terminal_translate_input
extern uart_receive_byte,uart_rx_buffer,uart_rx_count,uart_rx_read,uart_rx_write,uart_rx_mask
global _parent_table_address,_parent_begin,_parent_next
_parent_table_address: mov ax,terminal_translation_table
 ret
_parent_begin:
 push bp
 mov bp,sp
 push si
 push di
 push es
 push ds
 pop es
 mov si,[bp+4]
 mov cx,[bp+6]
 mov [uart_rx_count],cx
 mov di,uart_rx_buffer
 mov [uart_rx_read],di
 cld
 rep movsb
 mov [uart_rx_write],di
 mov word [terminal_translation_enabled],0
 mov word [uart_rx_mask],255
 cmp word [bp+8],1
 jne .seven
 mov word [terminal_translation_enabled],1
.seven:
 cmp word [bp+8],2
 jne .done
 mov word [uart_rx_mask],127
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
_parent_next:
 push bp
 push si
 push di
 push es
 call uart_receive_byte
 cmp ax,0xffff
 je .done
 call terminal_translate_input
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
; These dependencies of unrelated linked functions must never execute.
global _xlt_live_initialize,terminal_receive_character,pcplus_seconds,pcplus_flow_bell
global pcplus_flow_message,pcplus_escape_pressed,pcplus_screen_restore,pcplus_screen_save
_xlt_live_initialize:
terminal_receive_character:
pcplus_seconds:
pcplus_flow_bell:
pcplus_flow_message:
pcplus_escape_pressed:
pcplus_screen_restore:
pcplus_screen_save:
 int 3
 jmp $
SEGMENT _DATA public class=DATA use16
global terminal_option_mask,terminal_translation_path,process_psp,terminal_parser_active
global terminal_configuration_values
terminal_option_mask: dw 0
terminal_translation_path: db 0
process_psp: dw 0
terminal_parser_active: dw 0
terminal_configuration_values: dw 0
'''

DRIVER = r'''
#include <dos.h>
#include <conio.h>
#include <stdio.h>
#include <process.h>
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
#include "serial_handoff.h"
extern unsigned char *__cdecl parent_table_address(void);
extern void __cdecl parent_begin(const unsigned char *,unsigned,unsigned);
extern unsigned __cdecl parent_next(void);
static aspect_serial_handoff lease;
static struct {unsigned before;unsigned char bytes[4096];unsigned after;} ring;
int main(void){
 unsigned cfg[3],i,psp,ds,oldmcr,mask,vector_ok,mask_ok,mcr_ok,guard_ok,guard;
 unsigned ptr,mode;unsigned char *table;char option[32];FILE *file;
 int out,err,saveout,saveerr,result;union REGS inregs,outregs;
 void (__interrupt __far *vector)(void);
 file=fopen("POLICY.BIN","rb");if(!file)return 99;
 table=parent_table_address();if(fread(cfg,2,3,file)!=3||fread(table,1,256,file)!=256)return 98;fclose(file);
 inregs.h.ah=0x62;intdos(&inregs,&outregs);psp=outregs.x.bx;ds=FP_SEG((void __far *)&lease);
 lease.magic=ASIO_MAGIC;lease.version=cfg[0];lease.size=ASIO_SIZE;
 lease.parent_psp=psp;lease.parent_ds=ds;lease.ring=(unsigned)ring.bytes;lease.capacity=4096;
 mode=cfg[1];ptr=mode==1?(unsigned)table:0;
 switch(cfg[2]){
 case 2:mode=3;ptr=0;break;
 case 3:ptr=(unsigned)ring.bytes;break;
 case 4:ptr=(unsigned)&lease;break;
 case 5:ptr=0xff80;break;
 case 6:mode=0;ptr=(unsigned)table;break;
 case 7:mode=1;ptr=0;break;
 case 8:mode=2;ptr=(unsigned)table;break;
 }
 lease.reserved0=ptr;lease.reserved1=mode;
 guard=psp^ds^(unsigned)ring.bytes^ASIO_GUARD;
 if(lease.version==2)guard^=ptr^mode;
 if(cfg[2]==1)guard^=1;
 lease.guard=guard;ring.before=0x1234;ring.after=0x5678;
 sprintf(option,"/S1:0003:03:N:%04X:%04X",ds,(unsigned)&lease);
 oldmcr=inp(0x3fc);outp(0x3fc,oldmcr|1);mask=inp(0x21);vector=_dos_getvect(12);
 out=open("STDOUT.BIN",O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);
 err=open("STDERR.BIN",O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);
 if(out<0||err<0)return 97;saveout=dup(1);saveerr=dup(2);
 if(saveout<0||saveerr<0||dup2(out,1)||dup2(err,2))return 96;close(out);close(err);
 result=spawnl(P_WAIT,"ASPECT.EXE","ASPECT","CASE.ASX",option,(char *)0);
 dup2(saveout,1);dup2(saveerr,2);close(saveout);close(saveerr);
 vector_ok=_dos_getvect(12)==vector;mask_ok=inp(0x21)==mask;
 mcr_ok=inp(0x3fc)==(oldmcr|1);outp(0x3fc,oldmcr);
 guard_ok=ring.before==0x1234&&ring.after==0x5678&&lease.guard==guard&&lease.reserved0==ptr&&lease.reserved1==mode;
 file=fopen("RETURN.BIN","wb");if(!file)return 95;
 if(lease.count<=4096)fwrite(ring.bytes,1,lease.count,file);fclose(file);
 file=fopen("MAPPED.BIN","wb");if(!file)return 95;
 if(lease.count<=4096){parent_begin(ring.bytes,lease.count,cfg[1]);for(i=0;i<lease.count;++i)fputc(parent_next(),file);}fclose(file);
 file=fopen("LEASE.BIN","wb");if(!file)return 95;fwrite(&lease,1,sizeof(lease),file);fclose(file);
 file=fopen("STATUS.TXT","w");if(!file)return 95;
 fprintf(file,"exit=%d vector=%u mask=%u mcr=%u returned=%u count=%u lease=%u guard=%u\n",
 result,vector_ok,mask_ok,mcr_ok,lease.returned,lease.count,lease.status,guard_ok);fclose(file);
 return vector_ok&&mask_ok&&mcr_ok&&guard_ok?0:94;
}
'''


def definitions():
    cases = []
    scalar = 'integer value\nstring displaybuf'
    show = '\nitoa value displaybuf\nmessage displaybuf'
    chain = {65: 66, 66: 67}

    def add(name, decl, body, data, stdout, *, mode=1, version=2, table=None,
            raw=b'', mapped=b'', bad=0, error=0):
        source = decl + '\nproc main\n' + body + '\nendproc\n'
        cases.append(dict(name=name, source=source.replace('\n', '\r\n'), data=data,
                          stdout=stdout, mode=mode, version=version,
                          table=chain if table is None else table, raw=raw, mapped=mapped, bad=bad, error=error))

    pair = 'transmit "READY^M"\npause 1\ncomgetc value' + show + '\ncomgetc value' + show
    add('IDENTV1', scalar, pair, b'AB', b'65\r\n66\r\n', mode=0, version=1)
    add('IDENTV2', scalar, pair, b'AB', b'65\r\n66\r\n', mode=0)
    add('TABLEGC', scalar, pair, b'AB', b'66\r\n67\r\n')
    add('TABLECD', scalar, 'transmit "READY^M"\ncomgetcd value' + show, b'A', b'66\r\n')
    add('EMPTYCD', scalar, 'comgetcd value' + show, b'', b'-1\r\n', table={255: 88})
    add('MAPNUL', scalar, 'transmit "READY^M"\ncomgetcd value' + show, b'A', b'0\r\n', table={65: 0})
    add('MAPHIGH', scalar, 'transmit "READY^M"\ncomgetcd value' + show, b'A', b'255\r\n', table={65: 255})
    add('RGCRTAIL', 'string buffer', 'transmit "READY^M"\nrget buffer 5 3\npause 1\nmessage buffer',
        b'AXAB', b'B\r\n', table={65: 66, 66: 67, 88: 13}, raw=b'AB', mapped=b'BC')
    add('RGNUL', scalar + '\nstring buffer', 'transmit "READY^M"\nrget buffer 5 3\n'
        'strpeek buffer 0 value' + show + '\nstrpeek buffer 1 value' + show,
        b'ABX', b'0\r\n255\r\n', table={65: 0, 66: 255, 88: 13})
    add('SEVEN', scalar, pair + '\ncomgetc value' + show, bytes.fromhex('c1c2ff'),
        b'65\r\n66\r\n127\r\n', mode=2)
    add('SEVTAIL', 'string buffer', 'transmit "READY^M"\nrget buffer 5 3\npause 1\nmessage buffer',
        bytes.fromhex('c18dc2'), b'A\r\n', mode=2, raw=bytes.fromhex('c2'), mapped=b'B')
    add('WAITMAP', scalar, 'transmit "READY^M"\nwaitfor "BC" 3\nvalue = WAITFOR' + show,
        b'AB', b'1\r\n')
    add('WAITTAIL', scalar, 'transmit "READY^M"\nwaitfor "B" 3\npause 1\nvalue = WAITFOR' + show,
        b'XA', b'1\r\n', table={88: 66, 66: 67, 65: 0}, raw=b'A', mapped=b'\0')
    add('WAITDRN', scalar, 'transmit "READY^M"\nwaitquiet 1 3\nvalue = failure' + show +
        '\nvalue = COMDATA' + show, b'AB', b'0\r\n0\r\n', table={65: 0, 66: 67})
    add('GUARDCR', 'string buffer', 'transmit "READY^M"\nrget buffer 0 3\npause 1\nmessage "SAFE"',
        b'X' * 80 + b'ATRAIL', b'SAFE\r\n', table={65: 13}, raw=b'TRAIL', mapped=b'TR\rIL')
    add('GUARDRAW', 'string buffer', 'transmit "READY^M"\nrget buffer 0 3\nmessage "UNREACHABLE"',
        b'X' * 80 + b'\rTRAIL', b'', table={13: 65}, raw=b'TRAIL', mapped=b'TRAIL', error=7)
    for bad, name in [(1, 'BADGUARD'), (2, 'BADMODE'), (3, 'RINGPTR'), (4, 'DESCPTR'),
                      (5, 'WRAPPTR'), (6, 'IDPTR'), (7, 'V1RES'), (8, 'SEVPTR')]:
        add(name, '', 'transmit "UNREACHABLE"\nmessage "UNREACHABLE"', b'', b'',
            bad=bad, version=1 if bad == 7 else 2)
    return cases


def build_parent(output):
    output.mkdir(parents=True, exist_ok=True)
    (output / 'parent.c').write_text(DRIVER)
    (output / 'adapter.asm').write_text(ADAPTER)
    sources = [ROOT / 'reconstruction/uart/core.asm', ROOT / 'src/terminal/uart_data.asm',
               ROOT / 'src/terminal/translation.asm', output / 'adapter.asm']
    objects = []
    for index, source in enumerate(sources):
        obj = output / f'unit{index}.obj'
        subprocess.run(['nasm', '-f', 'obj', '-DUART_OMF', '-I' + str(ROOT / 'reconstruction/uart') + '/',
                        '-I' + str(ROOT / 'src/config') + '/', str(source), '-o', str(obj)], check=True)
        objects.append(str(obj))
    parent_obj = output / 'parent.obj'
    subprocess.run(['wcc', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we',
                    '-i=' + str(ROOT / 'src/aspect'), '-fo=' + str(parent_obj), str(output / 'parent.c')],
                   cwd=output, check=True)
    # Actual terminal assembly uses DATA-relative offsets; preserve its linked
    # class order so compiler CONST strings cannot move DGROUP before DATA.
    subprocess.run(['wlink', 'system', 'dos', 'order', 'clname', 'CODE', 'clname', 'DATA',
                    'clname', 'BSS', 'clname', 'STACK', 'option', 'quiet', 'option', 'stack=4096',
                    'option', 'map=' + str(output / 'parent.map'), 'name', str(output / 'XLTPAR.EXE'),
                    'file', ','.join([*objects, str(parent_obj)]), 'library',
                    str(Path(os.environ['WATCOM']) / 'lib286/dos/clibs.lib')], cwd=output, check=True)
    return sources


def run(case, binary, output):
    folder = output / case['name'];folder.mkdir(parents=True, exist_ok=True)
    for item in ('STATUS.TXT', 'STDOUT.BIN', 'STDERR.BIN', 'RETURN.BIN', 'MAPPED.BIN', 'LEASE.BIN'):
        (folder / item).unlink(missing_ok=True)
    shutil.copyfile(binary, folder / 'ASPECT.EXE')
    shutil.copyfile(output / 'XLTPAR.EXE', folder / 'XLTPAR.EXE')
    table = bytearray(range(256))
    for before, after in case['table'].items():table[before] = after
    (folder / 'POLICY.BIN').write_bytes(struct.pack('<HHH', case['version'], case['mode'], case['bad']) + table)
    (folder / 'CASE.ASP').write_bytes(case['source'].encode('cp437'))
    (folder / 'CASE.ASX').write_bytes(compile_source(case['source']))
    tx, errors = bytearray(), []
    stop, sent = threading.Event(), threading.Event()
    server = socket.socket();server.bind(('127.0.0.1', 0));server.listen(1);server.settimeout(12)

    def peer():
        try:
            conn, _ = server.accept()
            with conn:
                conn.settimeout(0.02);conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                trigger = None
                while not stop.is_set():
                    if b'READY\r' in tx and trigger is None:trigger = time.monotonic()
                    if case['data'] and not sent.is_set() and trigger is not None and time.monotonic()-trigger>=0.1:
                        conn.sendall(case['data']);sent.set()
                    try:
                        chunk = conn.recv(4096)
                        if not chunk:break
                        tx.extend(chunk)
                    except socket.timeout:pass
        except OSError as error:
            if not stop.is_set():errors.append(str(error))

    worker = threading.Thread(target=peer, daemon=True);worker.start()
    config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{folder}"
c:
XLTPAR
exit
'''
    (folder / 'dosbox.conf').write_text(config)
    try:
        with (folder / 'dosbox.log').open('w') as log:
            subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(folder / 'dosbox.conf')],
                           stdout=log, stderr=log, timeout=15, check=True,
                           env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
    finally:
        stop.set();server.close();worker.join(timeout=1)
    status = (folder / 'STATUS.TXT').read_text().strip()
    stdout, stderr = (folder / 'STDOUT.BIN').read_bytes(), (folder / 'STDERR.BIN').read_bytes()
    raw, mapped = (folder / 'RETURN.BIN').read_bytes(), (folder / 'MAPPED.BIN').read_bytes()
    bad = bool(case['bad'])
    expected_status = (f'exit={14 if bad else case["error"]} vector=1 mask=1 mcr=1 returned={0 if bad else 1} '
                       f'count={len(case["raw"])} lease=0 guard=1')
    checks = dict(resources_and_publication=status == expected_status,
                  exact_stdout=stdout == case['stdout'],
                  exact_tx=bytes(tx) == (b'' if bad or 'transmit' not in case['source'] else b'READY\r'),
                  exact_raw_handback=raw == case['raw'],
                  actual_parent_once_mapping=mapped == case['mapped'],
                  rejected_before_execution=(b'serial 1' in stderr and b'step 0' in stderr) if bad else
                  (b'error 7' in stderr and b'native ' not in stderr) if case['error'] else stderr == b'',
                  no_peer_error=not errors, stimulus_sent=sent.is_set() if case['data'] else True)
    (folder / 'transmitted.bin').write_bytes(tx)
    report = dict(name=case['name'], passed=all(checks.values()), checks=checks, status=status,
                  source_sha256=sha(folder / 'CASE.ASP'), asx_sha256=sha(folder / 'CASE.ASX'),
                  policy_sha256=sha(folder / 'POLICY.BIN'), runner_sha256=sha(folder / 'ASPECT.EXE'),
                  parent_sha256=sha(folder / 'XLTPAR.EXE'), config_sha256=sha(folder / 'dosbox.conf'),
                  stdout_hex=stdout.hex(), stderr_hex=stderr.hex(), tx_hex=bytes(tx).hex(),
                  raw_hex=raw.hex(), parent_mapped_hex=mapped.hex(), peer_errors=errors)
    (folder / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(case['name'], 'PASS' if report['passed'] else checks, flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runner', type=Path, default=ROOT / 'build/aspect-runner/ASPECT.EXE')
    parser.add_argument('--case', action='append')
    args = parser.parse_args()
    assert args.runner.is_file() and not args.runner.name.lower().endswith('.analysis.exe')
    cases = definitions()
    if args.case:
        cases = [case for case in cases if case['name'] in args.case]
        assert {case['name'] for case in cases} == set(args.case)
    output = ROOT / 'build/aspect-script-translation-dos'
    sources = build_parent(output)
    runner_hash = sha(args.runner);manifest = args.runner.parent / 'manifest.json'
    assert json.loads(manifest.read_text())['binary_sha256'] == runner_hash
    predictions = [{key: value.hex() if isinstance(value, bytes) else value
                    for key, value in case.items()} for case in cases]
    (output / 'predictions.json').write_text(json.dumps(predictions, indent=2) + '\n')
    results = [run(case, args.runner, output) for case in cases]
    assert all(result['runner_sha256'] == runner_hash for result in results)
    report = dict(passed=all(result['passed'] for result in results), original_inputs=[],
                  checker_sha256=sha(Path(__file__)), compiler_sha256=sha(ROOT / 'src/aspect/compiler.py'),
                  runner_sha256=runner_hash, runner_manifest_sha256=sha(manifest),
                  predictions_sha256=sha(output / 'predictions.json'),
                  parent_sha256=sha(output / 'XLTPAR.EXE'), parent_source_sha256=sha(output / 'parent.c'),
                  handoff_header_sha256=sha(ROOT / 'src/aspect/serial_handoff.h'),
                  parent_sources={str(p.relative_to(ROOT)): sha(p) for p in sources}, cases=results,
                  scope='Actual COM1/38400/8N1/flowN DOS scripts with independent raw peer and ASIOv1/v2 parent. '
                  'Returned bytes traverse actual source-built UART dequeue+terminal_translate_input once; no duplicate parent mapper. '
                  'Unused init/render callbacks trap, no terminal parser/UI/BBS/physical-modem or full application gate claim.')
    (output / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    assert report['passed'], 'Translation DOS checks failed; every attempted case retained.'
    print(f'{len(results)} actual DOS translation cases passed')


if __name__ == '__main__':
    main()
