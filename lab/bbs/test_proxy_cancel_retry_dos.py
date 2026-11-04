#!/usr/bin/env python3
"""Cancel actual stock Enigma ZMODEM, list, retry and list in one DOS process.

Actual staged size-probed proxy/serial-side path; no SIP/DSP/physical DCD claim.
"""
import argparse
import asyncio
import contextlib
import fcntl
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import time

import test_dos
from product_inputs import ROOT,select_product,sha
from enigma import SOURCE,process_pid
from test_proxy_transfer_dos import post_count
from test_transfer_dos import ObservedModem,timestamp,offset_after
from audit_zmodem import scan,packet,metadata,audit_batch,audit_controls
from audit_size_probe_screen import telnet
from paced_bios_keys import source as keyboard_source,entries
from zmodem_cancel_disk_watch import SAMPLER


async def run(a):
    assert re.fullmatch('[a-z0-9-]+',a.label) and re.fullmatch(r'P[A-F0-9]{6}\.BIN',a.file)
    assert process_pid(),'Owned stock Enigma must be running'
    lock=(ROOT/'build/bbs-lab/enigma/.dos-integration.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    binary,inputs=select_product(a.terminal,'TERMINAL.EXE')
    payload_path=SOURCE/'file_base/pcplus_transfer'/a.file;payload=payload_path.read_bytes()
    assert len(payload)==65539 and set(payload)==set(range(256))
    out=ROOT/'build/bbs-lab/results/enigma'/a.label;out.mkdir(parents=True,exist_ok=False)
    recv=out/'RECV';recv.mkdir();stage=out/'program';stage.mkdir()
    shutil.copyfile(binary,stage/'TERMINAL.EXE')
    prefix=json.loads((ROOT/'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
    prefix=prefix[:prefix.index('M enter')].replace('n p6000 n p3000 enter','n p6000 enter')
    filename=' '.join(a.file)
    recipe=('p1900 enter p2500 l o c enter '+prefix+'c-y p2000 F enter p2000 '+
        'S enter p2000 '+filename+' enter p1500 enter p2000 t p1500 q p1500 escape '+
        'p1000 D enter p2000 a p1500 enter '+
        'p35000 enter p2000 L enter p1500 escape p1500 escape p1500 S enter p1500 '+filename+' enter p1500 enter p1500 '+
        'escape p1500 escape p1500 D enter p2000 a p1500 enter '+
        'p60000 enter p2000 L enter p1500 escape p1500 escape p1500 S enter p1500 '+filename+' enter p1500 enter p4000 a-x')
    (out/'recipe.json').write_text(json.dumps(dict(recipe=recipe,BIOS_entries=entries(recipe)),indent=2)+'\n')
    (out/'KEYS.ASM').write_text(keyboard_source(recipe))
    subprocess.run(['nasm','-fbin',str(out/'KEYS.ASM'),'-o',str(out/'PACED.COM')],check=True)
    product_names=['test_proxy_cancel_retry_dos','paced_bios_keys','test_dos','test_proxy_transfer_dos',
                   'test_transfer_dos','modem','audit_zmodem','audit_size_probe_screen','zmodem_cancel_watch','zmodem_label_watch','zmodem_cancel_disk_watch']
    inputs += [ROOT/'lab/bbs'/(n+'.py') for n in product_names]
    inputs += [ROOT/'lab/bbs/synthmodem_proxy_serial.js',ROOT/'lab/bbs/editor-recipes.json',
               ROOT/'standalone/test_terminal.py',ROOT/'standalone/display_startup_geometry.asm',
               payload_path,stage/'TERMINAL.EXE',out/'KEYS.ASM',out/'PACED.COM',out/'recipe.json']
    server=[SOURCE/n for n in ['main.js','core/client.js','core/file_transfer.js','core/file_entry.js',
        'core/download_queue.js','core/file_area_list.js','core/file_base_search.js','core/menu_module.js','core/user_interrupt_queue.js',
        'config/menus/loc-file_base.hjson','config/config.hjson','package-lock.json']]+[SOURCE.parent/'helpers/sexyz']
    inputs+=server
    frozen={str(p.relative_to(ROOT)):sha(p) for p in inputs};posts=post_count()
    bridge=ROOT/'build/bbs-lab'/(a.label+'-proxy')
    proxy=subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_proxy_serial.js'),'--runtime',str(a.runtime.resolve()),
        '--output',str(bridge),'--bbs-port','23233','--framing-ms','250','--byte-delay-ms','0',
        '--terminal-rows','24','--probe-terminal-size'],stderr=(out/'proxy.log').open('w'),stdout=subprocess.DEVNULL)
    observed=[];snapshots=[];done=asyncio.Event()
    class Observer(ObservedModem):
        def __init__(self,*args,**kw):
            kw['guarded_hangup_seconds']=.5
            super().__init__(*args,**kw);observed.append(self)
    original=(test_dos.Modem,test_dos.modem_fixture,test_dos.SAMPLER)
    def settings(**kw):
        data=bytearray(original[1](**kw));struct.pack_into('<H',data,0x42c,1)
        path=b'D:\\RECV\\\0';data[0x31c:0x31c+len(path)]=path
        return bytes(data)
    async def watch():
        partial_seen=False;clean_seen=False
        while not done.is_set():
            partial=recv/'PCRX.$$$'
            cancel_seen=bool(observed and b'\x18'*8+b'\x08'*10 in bytes(observed[0].keyboard))
            if observed and not cancel_seen and not partial_seen and partial.exists():
                data=partial.read_bytes()
                if data:
                    snapshots.append(dict(kind='partial',before_cancel=True,seconds=time.monotonic()-observed[0].start,length=len(data),source_prefix=data==payload[:len(data)],sha256=hashlib.sha256(data).hexdigest()))
                    partial_seen=True
            if observed and not clean_seen:
                raw=bytes(observed[0].keyboard);cancel=raw.find(b'\x18'*8+b'\x08'*10)
                if cancel>=0 and raw.find(b'\x1b\x1bS\r',cancel+18)>=0:
                    snapshots.append(dict(kind='after-cancel-before-retry',seconds=time.monotonic()-observed[0].start,files={p.name:sha(p) for p in recv.iterdir()}));clean_seen=True
            await asyncio.sleep(.01)
    task=None
    try:
        deadline=time.monotonic()+15
        while not (bridge/'ready.json').exists():
            assert proxy.poll() is None and time.monotonic()<deadline
            await asyncio.sleep(.05)
        ready=json.loads((bridge/'ready.json').read_text())
        test_dos.Modem=Observer;test_dos.modem_fixture=settings
        # Visible count>=8KiB permits a nonempty DOS stage before Escape.
        test_dos.SAMPLER=SAMPLER
        task=asyncio.create_task(watch())
        options=argparse.Namespace(name='enigma',label=a.label,port=ready['endpoint']['port'],com=3,irq=5,
            baud=19200,flow='HARD',packet_delay_ms=0,dial_fixture=True,directory_fixture=False,directory_browser=False,
            entry=3,binary=stage/'TERMINAL.EXE',config_fixture=False,keymap_fixture=None,
            server_log=SOURCE/'logs/enigma-bbs.log',keys='p300000',wait=0,timeout=330,cpu='8086',
            mouse_scales=(8,4),display_rows=25,status_hidden=0,raw_upstream=True,phone_log=True,
            keyboard_helper=out/'PACED.COM')
        with (out/'harness.log').open('w') as log,contextlib.redirect_stdout(log):code=await test_dos.run(options)
        assert len(observed)==1
        modem=observed[0];stream=bytes(modem.display);keyboard=bytes(modem.keyboard)
        (out/'trace.json').write_text(json.dumps(modem.trace,indent=2)+'\n')
        (out/'cancel-snapshots.json').write_text(json.dumps(snapshots,indent=2)+'\n')
        deadline=time.monotonic()+5
        while not (bridge/'1-closed.json').exists() and time.monotonic()<deadline:await asyncio.sleep(.05)
        harness=json.loads((out/'result.json').read_text())
        closed=json.loads((bridge/'1-closed.json').read_text())
        checks=dict(DOS_harness=code==0 and harness['passed'],sources_unchanged=all(sha(ROOT/n)==h for n,h in frozen.items()),
            no_post_saved=posts==post_count(),exact_retry=(recv/a.file).is_file() and (recv/a.file).read_bytes()==payload,
            only_expected_received_files={p.name for p in recv.iterdir()}=={a.file},
            partial_observed=any(s['kind']=='partial' and s['before_cancel'] and s['source_prefix'] and 0<s['length']<len(payload) for s in snapshots),
            cleaned_before_retry=any(s['kind']=='after-cancel-before-retry' and s['files']=={} for s in snapshots),
            exact_proxy_input=(bridge/'1-serial-input.bin').read_bytes()==(out/'bbs-sent.bin').read_bytes(),
            exact_proxy_output=(bridge/'1-serial-output.bin').read_bytes()==(out/'display.bin').read_bytes(),
            proxy_sources_unchanged=closed['source_unchanged'],one_connection=len([e for e in modem.events if e['kind']=='bbs-connected'])==1,
            decoded_offsets=modem.bbs_offset==len(stream) and modem.dos_offset==len(keyboard))
        errors=[];protocol={}
        try:
            labels=(out/'LABELS.BIN').read_bytes()
            assert len(labels)==2566 and struct.unpack_from('<H',labels)[0]==0x4e5a and struct.unpack_from('<H',labels,4)[0]&0x8000
            cancel=keyboard.index(b'\x18'*8+b'\x08'*10);cancel_time=timestamp(modem.trace,'dos',cancel)
            first=[h for h in scan(stream) if h['type']==4 and timestamp(modem.trace,'bbs',h['offset'])<cancel_time]
            assert first
            offer=packet(stream,first[0]['end'],first[0]['format']);assert metadata(offer['payload'])==(a.file,len(payload))
            data=[h for h in scan(stream) if h['type']==10 and first[0]['offset']<h['offset'] and timestamp(modem.trace,'bbs',h['offset'])<cancel_time]
            assert data
            body=packet(stream,data[0]['end'],data[0]['format'])['payload'];assert body and body==payload[:len(body)]
            assert not any(h['type']==11 and first[0]['offset']<h['offset'] and timestamp(modem.trace,'bbs',h['offset'])<cancel_time for h in scan(stream))
            list_at=keyboard.index(b'\x1b\x1bS\r',cancel+18);list_time=timestamp(modem.trace,'dos',list_at+2)
            retry_command=keyboard.index(b'D\r',list_at+4);retry_time=timestamp(modem.trace,'dos',retry_command)
            part=next(s for s in snapshots if s['kind']=='partial')
            clean=next(s for s in snapshots if s['kind']=='after-cancel-before-retry')
            assert part['seconds']<cancel_time<clean['seconds']<retry_time,'Partial/cleanup not ordered around cancel and retry'
            start=offset_after(modem.trace,'bbs',retry_time);assert start is not None
            retry=audit_batch(stream,{a.file:payload},start)
            list_start=offset_after(modem.trace,'bbs',list_time);assert list_start is not None
            assert (a.file+' ').encode() in stream[list_start:start],'No target file response before retry command'
            end_time=timestamp(modem.trace,'bbs',retry['end']-1)
            cut=offset_after(modem.trace,'dos',end_time);assert cut is not None
            final=keyboard.index(b'\x1b\x1bS\r',cut);final_time=timestamp(modem.trace,'dos',final+2)
            retry['controls']=audit_controls(retry,keyboard,modem.trace,'bbs',final_time,False)
            tail=offset_after(modem.trace,'bbs',final_time);assert tail is not None and (a.file+' ').encode() in stream[tail:],'No target file response after completed retry'
            client,subs,_=telnet((bridge/'1-telnet-input.bin').read_bytes());server,_,_=telnet((bridge/'1-telnet-output.bin').read_bytes())
            prefix=b'loc\r\x1b[8;24;80t';online=(out/'bbs-sent.bin').read_bytes()
            assert online.startswith(prefix) and client==online[len(prefix):] and stream.endswith(server),'Proxy changed online application bytes'
            before=b'ATZ\r'+f"ATDlab.local:{ready['endpoint']['port']}\r".encode()
            assert keyboard==before+online+b'+++ATH\r','Unexpected bytes outside modeled online lifetime'
            assert [list(struct.unpack('>HH',s[1:])) for s in subs if s[0]==31]==[[80,24]]
            for f in retry['files']:f.pop('source')
            protocol=dict(cancel_offset=cancel,first_offer=first[0],first_data_bytes=len(body),retry_command_offset=retry_command,retry=retry)
            checks['BIOS_cancel_during_data_list_retry_finish_list']=True
        except (AssertionError,ValueError,KeyError,TypeError,FileNotFoundError) as e:
            errors.append(str(e));checks['BIOS_cancel_during_data_list_retry_finish_list']=False
        boundary=json.loads((out/'server-log-start.json').read_text());log=Path(boundary['path']);assert log.stat().st_ino==boundary['inode']
        with log.open('rb') as f:f.seek(boundary['byte_offset']);rows=[json.loads(line) for line in f if line.strip()]
        sessions={r['sessionId'] for r in rows if r.get('msg')=='User "loclab" successfully logged in'}
        own=[r for r in rows if r.get('sessionId') in sessions]
        (out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in own))
        executions=[i for i,r in enumerate(own) if r.get('msg')=='Executing external protocol']
        exits=[(i,r.get('exitCode')) for i,r in enumerate(own) if r.get('msg')=='Process exited']
        checks['one_authenticated_two_helper_processes']=len(sessions)==1 and len(executions)==len(exits)==2 and executions[0]<exits[0][0]<executions[1]<exits[1][0] and exits[0][1]!=0 and exits[1][1]==0
        result=dict(passed=all(checks.values()) and not errors,checks=checks,errors=errors,protocol=protocol,
            terminal_sha256=sha(binary),sources=frozen,payload_name=a.file,payload_bytes=len(payload),payload_sha256=sha(payload_path),
            snapshots=snapshots,server_exit_codes=[v for _,v in exits],proxy=ready,
            scope=__doc__+' Current parent,8086 COM3/IRQ5,19200/HARD. Timer injects BIOS Escape after visible KiB; paced BIOS helper supplies navigation. Nullmodem CTS ready is not physical flow/DCD evidence.')
        (out/'cancel-checks.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(dict(passed=result['passed'],checks=checks,errors=errors),indent=2))
        return 0 if result['passed'] else 1
    finally:
        test_dos.Modem,test_dos.modem_fixture,test_dos.SAMPLER=original;done.set()
        if task:await task
        proxy.terminate()
        try:proxy.wait(timeout=5)
        except subprocess.TimeoutExpired:proxy.kill();proxy.wait()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['runtime','terminal']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--label',required=True);p.add_argument('--file',required=True)
    raise SystemExit(asyncio.run(run(p.parse_args())))
