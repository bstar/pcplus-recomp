#!/usr/bin/env python3
"""Actual DOS recorder files, DOS compilation and production UART script replay.

An owned diagnostic calls the same far-callable source recorder, then compiles
and runs its ASP. Loopback prompts and payloads are synthetic. This is not the
terminal's recording UI, shared file owner or physical modem acceptance.
"""
import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import threading
from pathlib import Path
from test_terminal import ROOT, SAMPLER


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


DRIVER = r'''
#include <stdio.h>
#include <string.h>
#include <dos.h>
#include <process.h>
#include "recorder.h"
static unsigned closed;
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify exact [ax];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify exact [ax];
static unsigned AR_FAR AR_CALL output(void *context,const void *data,unsigned count,unsigned *actual){
 FILE *file=context;*actual=fwrite(data,1,count,file);return ferror(file)?1:0;
}
static unsigned AR_FAR AR_CALL close_output(void *context){++closed;return fclose(context)!=0;}
int main(int argc,char **argv){
 static aspect_recorder session;
 aspect_recorder_ops ops;unsigned char bytes[40];unsigned n,status=0,recorded,expected=0;
 FILE *source,*input,*report;void (__interrupt __far *before)(void);
 before=_dos_getvect(0);ops.write=output;ops.close=close_output;
 if(!freopen("ERROR.TXT","wb",stderr))return 90;
 if(argc>1&&!strcmp(argv[1],"writefail")){
  source=fopen("REC.TMP","wb");if(!source)return 91;fwrite("KEEP",1,4,source);fclose(source);
  source=fopen("REC.TMP","rb");expected=AR_WRITE;
 }else source=fopen("REC.TMP","wb");
 if(!source)return 92;
 status=aspect_recorder_start(&session,&ops,source,1);
 if(!status)status=aspect_recorder_transmit(&session,"READY>",6);
 if(!status&&argc>1&&!strcmp(argv[1],"cancel")){
  status=aspect_recorder_cancel(&session);expected=AR_CANCELLED;
 }else if(!status){
  input=fopen("PROMPT.BIN","rb");if(!input)return 93;
  n=fread(bytes,1,16,input);fclose(input);
  if(n)status=aspect_recorder_receive(&session,bytes,n);
  input=fopen("PAYLOAD.BIN","rb");if(!input)return 94;
  while(!status&&(n=fread(bytes,1,40,input))!=0)status=aspect_recorder_transmit(&session,bytes,n);
  if(ferror(input))status=95;fclose(input);
 }
 recorded=aspect_recorder_stop(&session);
 if(recorded!=status&&status)return 96;
 status=recorded;
 if(!status){
  if(rename("REC.TMP","CASE.ASP"))return 97;
  if(spawnl(P_WAIT,"ASPCOMP.EXE","ASPCOMP","CASE.ASP","CASE.ASX",(char *)0))return 98;
  status=spawnl(P_WAIT,"ASPECT.EXE","ASPECT","CASE.ASX","/S1:0003:03:N",(char *)0);
 }else if(status==AR_CANCELLED){if(remove("REC.TMP"))return 99;}
 report=fopen("STATUS.TXT","w");if(!report)return 100;
 fprintf(report,"%u %u %u %u %lu %lu %lu\n",status,closed,_dos_getvect(0)==before,
  data_segment()==stack_segment(),session.transmitted_bytes,session.received_bytes,session.source_bytes);
 fclose(report);return status==expected?0:1;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    frozen = {}
    for directory, binary in [('aspect-runner', 'ASPECT.EXE'), ('aspect-compiler-dos', 'ASPCOMP.EXE')]:
        base = ROOT / 'build' / directory
        manifest = json.loads((base / 'manifest.json').read_text())
        assert not manifest['original_inputs'] and sha(base / binary) == manifest['binary_sha256']
        for name, digest in manifest['sources'].items():
            assert sha(ROOT / name) == digest, name
            assert name not in frozen or frozen[name] == digest
            frozen[name] = digest
        for path in [base / binary, base / 'manifest.json']:
            frozen[str(path.relative_to(ROOT))] = sha(path)
        shutil.copy2(base / binary, out / binary)
    for path in [Path(__file__).resolve(), ROOT / 'src/aspect/recorder.c', ROOT / 'src/aspect/recorder.h', ROOT / 'standalone/test_terminal.py']:
        frozen[str(path.relative_to(ROOT))] = sha(path)
    for name, digest in frozen.items():
        copy = out / 'frozen-source' / name
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, copy)
        assert sha(copy) == digest
    (out / 'start.json').write_text(json.dumps(dict(inputs=frozen), indent=2) + '\n')
    (out / 'driver.c').write_text(DRIVER)
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we', '-k8192',
                    '-i=' + str(ROOT / 'src/aspect'), '-fm=RECORD.map', '-fe=RECORD.EXE',
                    str(out / 'driver.c'), str(ROOT / 'src/aspect/recorder.c')], cwd=out, check=True)
    (out / 'sampler.asm').write_text(SAMPLER)
    (out / 'setup.asm').write_text('BITS 16\nCPU 8086\nORG 100h\nmov dx,3fbh\nmov al,80h\nout dx,al\nmov dx,3f8h\nmov al,12\nout dx,al\ninc dx\nxor al,al\nout dx,al\nmov dx,3fbh\nmov al,3\nout dx,al\nmov dx,3fch\nmov al,1\nout dx,al\nmov ax,4c00h\nint 21h\n')
    for source, binary in [('sampler', 'SNAP'), ('setup', 'SETUP')]:
        subprocess.run(['nasm', '-fbin', str(out / (source + '.asm')), '-o', str(out / (binary + '.COM'))], check=True)
    cases = [
        ('ordinary', b'Name? ', bytes(range(256)), b'Name? ', 0),
        ('quoted-controls', b'\r\n"^>\x1e\x1f\xff', bytes(range(256)), b'\r\n"^>\x1e\x1f\xff', 0),
        ('long-control-prompt', bytes(range(1, 17)), bytes(range(256)) * 8, bytes(range(1, 17)), 0),
        ('timeout-no-payload', b'Name? ', b'MUST NOT SEND', b'Wrong! ', 0),
        ('writefail', b'', b'', b'', 3),
        ('cancel', b'', b'', b'', 5),
    ]
    results = []
    for name, prompt, payload, reply, expected_status in cases:
        folder = out / name
        folder.mkdir()
        for binary in ('ASPECT.EXE', 'ASPCOMP.EXE', 'RECORD.EXE', 'SETUP.COM', 'SNAP.COM'):
            shutil.copy2(out / binary, folder / binary)
        (folder / 'PROMPT.BIN').write_bytes(prompt)
        (folder / 'PAYLOAD.BIN').write_bytes(payload)
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        listener.settimeout(15)
        wire = bytearray()
        errors = []
        sent = []
        port = listener.getsockname()[1]
        def peer():
            try:
                connection, _ = listener.accept()
                with connection:
                    connection.settimeout(15)
                    while True:
                        data = connection.recv(4096)
                        if not data:
                            break
                        wire.extend(data)
                        if reply and b'READY>' in wire and not sent:
                            connection.sendall(reply)
                            sent.append(reply.hex())
            except (OSError, TimeoutError) as exc:
                errors.append(repr(exc))
            finally:
                listener.close()
        thread = threading.Thread(target=peer, daemon=True)
        thread.start()
        config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{port} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{folder}"
mount d "{folder}"
d:
SETUP
SNAP B
RECORD {name if expected_status else ''} >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto finish
:failed
echo FAIL>FAIL.TXT
:finish
SNAP A
exit
'''
        (folder / 'dosbox.conf').write_text(config)
        with (folder / 'dosbox.log').open('w') as log:
            process = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(folder / 'dosbox.conf')],
                                     env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                                     stdout=log, stderr=log, timeout=45)
        thread.join(3)
        assert not thread.is_alive(), 'Owned peer did not exit'
        (folder / 'wire.bin').write_bytes(wire)
        (folder / 'peer-reply.bin').write_bytes(b''.join(bytes.fromhex(value) for value in sent))
        status = list(map(int, (folder / 'STATUS.TXT').read_text().split()))
        expected = b'' if expected_status else b'READY>' + (b'' if name == 'timeout-no-payload' else payload)
        checks = dict(DOS_normal_exit=process.returncode == 0 and (folder / 'PASS.TXT').exists() and not (folder / 'FAIL.TXT').exists(),
                      expected_status_and_one_close=status[:4] == [expected_status, 1, 1, 1],
                      exact_UART_bytes=bytes(wire) == expected, no_peer_errors=not errors,
                      expected_prompt_reply=sent == ([reply.hex()] if reply else []),
                      hardware_restored=(folder / 'BEFORE.BIN').read_bytes() == (folder / 'AFTER.BIN').read_bytes() and (folder / 'BEFORE.BIN').stat().st_size == 42,
                      no_script_runtime_errors=not (folder / 'ERROR.TXT').read_bytes())
        if not expected_status:
            checks['source_size_accounted'] = (folder / 'CASE.ASP').stat().st_size == status[6]
            checks['exact_recorded_input_counts'] = status[4:6] == [6 + len(payload), len(prompt)]
            checks['only_completed_source_published'] = (folder / 'CASE.ASP').is_file() and (folder / 'CASE.ASX').is_file() and not (folder / 'REC.TMP').exists()
        else:
            checks['no_source_or_bytecode_published'] = not (folder / 'CASE.ASP').exists() and not (folder / 'CASE.ASX').exists()
            checks['failed_stage_preserved_or_cancelled_stage_removed'] = (folder / 'REC.TMP').read_bytes() == b'KEEP' if name == 'writefail' else not (folder / 'REC.TMP').exists()
        result = dict(passed=all(checks.values()), case=name, checks=checks, status=status,
                      actual_hex=bytes(wire).hex(), expected_hex=expected.hex(), peer_replies=sent, peer_errors=errors)
        (folder / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        results.append(result)
        print(json.dumps(dict(case=name, passed=result['passed'], bytes=len(wire))), flush=True)
    for name, digest in frozen.items():
        assert sha(ROOT / name) == sha(out / 'frozen-source' / name) == digest, name
    result = dict(passed=all(case['passed'] for case in results), cases=results, inputs=frozen,
                  binary_sha256=sha(out / 'RECORD.EXE'), captures_sha256={str(path.relative_to(out)): sha(path) for path in out.rglob('*')
                                  if path.is_file() and not path.is_relative_to(out / 'frozen-source')}, scope=__doc__)
    with (out / 'result.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    assert result['passed'], [(case['case'], case['checks']) for case in results if not case['passed']]


if __name__ == '__main__':
    main()
