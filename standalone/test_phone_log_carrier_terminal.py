#!/usr/bin/env python3
"""Real emulated DCD loss and same-parent redial with checked call logging."""
import argparse,asyncio,binascii,datetime as dt,json,os,re,shutil,struct,subprocess,sys,time
from pathlib import Path
from build_phone_log_queue import ROOT,sha
from directory_fixtures import directory,prm
from directory_test_support import accounting_check
from test_terminal import SAMPLER
from test_phone_log_events_terminal import HEADING,OLD_CALL,inspect_disk_record
sys.path.insert(0,str(ROOT/'lab/bbs'))
from phone_log_evidence import build_observer


async def run_case(parent,out,name,ticks,soft,aspect=None,transfer=None):
    out.mkdir(parents=True);binary=parent/'TERMINAL.EXE'
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(parent/'terminal.map').read_text(),re.M|re.I)}
    stage=parent;extra_command='';keys='p900 enter p6000 a-d p4500 r e a d y p1800 a-x';extra_observer={};aspect_inputs=[]
    if aspect:
        runner=aspect['runner'];stage=out/'PARENT';stage.mkdir()
        for source in (binary,runner):shutil.copyfile(source,stage/source.name)
        extra_command=' /T:D:\\ACTIONS.KEY'
        keys='p900 enter p2500 a-1 '+('p600 a-z ' if aspect['window'] else '')+'p10000 a-d p4500 r e a d y p1800 a-x'
        sys.path.insert(0,str(ROOT/'src/aspect'))
        from compiler import compile_source
        from test_directory_key_bindings_dos import actions
        script='proc main\nfopen 4 "D:\\CHILD.LOG" "wb"\nfputs 4 "START|"\n'
        if aspect['handler']:script+='when disconnect call lost\n'
        script+='pause 2\ntransmit "SCRIPTREADY^M"\nwaitfor "NEVER" 3\nif waitfor\nfputs 4 "BAD|"\nelse\nfputs 4 "RETURN|"\nendif\nfclose 4\nendproc\n'
        if aspect['handler']:script+='proc lost\nfputs 4 "LOST|"\nfclose 4\nexit\nendproc\n'
        (out/'CARRY.ASP').write_text(script);(out/'CARRY.ASX').write_bytes(compile_source(script))
        (out/'ACTIONS.KEY').write_bytes(actions(b'D:\\CARRY.ASX',0))
        aspect_inputs=[stage/'TERMINAL.EXE',stage/'ASPECT.EXE',out/'CARRY.ASP',out/'CARRY.ASX',out/'ACTIONS.KEY']
        child={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(runner.parent/'ASPECT.map').read_text(),re.M|re.I)}
        extra_observer=dict(ASPECT_CHILD=1,PARENT_ASPECT_ACTIVE=symbols['terminal_aspect_active'][1],
            PARENT_ASPECT_SEG=symbols['render_child_ds'][0],PARENT_CHILD_DS=symbols['render_child_ds'][1],
            PARENT_WINDOW_ACTIVE=symbols['terminal_script_window_active'][1],PARENT_WINDOW_VISIBLE=symbols['terminal_script_overlay_visible'][1],
            CHILD_DATA_SEG=child['_runtime_error'][0],CHILD_ISR_SEG=child['uart_receive_interrupt'][0],CHILD_ISR_OFFSET=child['uart_receive_interrupt'][1],
            CHILD_EXIT_SEG=struct.unpack_from('<14H',runner.read_bytes())[11],
            CHILD_ARMED=child['_runtime_when_disconnect_armed'][1],CHILD_ERROR=child['_runtime_error'][1],
            CHILD_OPCODE=child['_runtime_last_opcode'][1],CHILD_MSR_PORT=child['uart_port_msr'][1])
        assert all(symbols[n][0]==extra_observer['PARENT_ASPECT_SEG'] for n in ('terminal_script_window_active','terminal_script_overlay_visible'))
    upload_body=bytes(65+i%26 for i in range(4096))
    if transfer:
        if transfer.get('strict'):extra_command+=' /I:1'
        upload=transfer['upload'];batch=transfer.get('protocol',0)
        if batch:(out/'RECV').mkdir()
        keys='p900 enter p2500 '+('a-s' if upload else 'a-r')+' p300 '+ ('f2 p100 '*batch)+ ' '.join('D:\\SEND.BIN' if upload else 'D:\\RECV\\' if batch else 'D:\\RECV.BIN')+' enter p14500 a-d p4500 r e a d y p1800 a-x'
        if upload:(out/'SEND.BIN').write_bytes(upload_body);aspect_inputs.append(out/'SEND.BIN')
        names=dict(TRANSFER_ACTIVE='terminal_transfer_active',TRANSFER_FAULT='terminal_transfer_fault',TRANSFER_CLEANUP='terminal_transfer_cleanup_status',
            TRANSFER_DIRECTION='terminal_transfer_direction',TRANSFER_RX_DROPPED='uart_rx_dropped',TRANSFER_PENDING='terminal_transfer_pending',
            TRANSFER_DOWNLOAD='_transfer_download_result',TRANSFER_UPLOAD='_upload_source_result',TRANSFER_MSR_PORT='uart_port_msr')
        assert all(symbols[n][0]==symbols['terminal_transfer_active'][0] for n in names.values())
        extra_observer=dict(TRANSFER_WATCH=1,**{key:symbols[n][1] for key,n in names.items()})
        if batch:
            batch_names=dict(BATCH_PROTOCOL='terminal_transfer_protocol',BATCH_DOWNLOAD='_batch_download_result',BATCH_UPLOAD='_batch_upload_current',BATCH_YMODEM='_ymodem_current',BATCH_ZFILES='_terminal_zmodem_files')
            assert all(symbols[n][0]==symbols['terminal_transfer_active'][0] for n in batch_names.values())
            extra_observer.update(TRANSFER_BATCH=1,**{key:symbols[n][1] for key,n in batch_names.items()})
    observer=build_observer(binary,out/'PLWATCH.COM',irq=5,extra=extra_observer)
    defines=dict(CARRIER=1,DELAY_TICKS=ticks,MCR_PORT=0x3ec,HARDWARE_ACTIVE_OFFSET=symbols['hardware_active'][1],
        RX_COUNT_OFFSET=symbols['uart_rx_count'][1],RX_DROPPED_OFFSET=symbols['uart_rx_dropped'][1],MSR_PORT_OFFSET=symbols['uart_port_msr'][1],
        LIFECYCLE_OFFSET=symbols['_phone_log_lifecycle_store'][1])
    subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in defines.items()],str(ROOT/'standalone/phone_log_slow_write.asm'),'-o',str(out/'SLOWLOG.COM')],check=True)
    seed=HEADING+OLD_CALL;(out/'PCPLUS.FON').write_bytes(seed)
    sampler=SAMPLER
    for offset in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+offset),hex(0x3e8+offset))
    (out/'sampler.asm').write_text(sampler)
    subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
    sessions=[];owners=set();started=time.monotonic()
    async def peer(reader,writer):
        task=asyncio.current_task();owners.add(task)
        item=dict(index=len(sessions)+1,received=bytearray(),events=[],errors=[]);sessions.append(item)
        def event(kind):item['events'].append({'kind':kind,'seconds':round(time.monotonic()-started,4)})
        try:
            event('connected')
            banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c'
            if item['index']==2:banner+=b'\x1b[2;1HREDIAL OK\x1b[6n'
            writer.write(banner);await writer.drain()
            if transfer and item['index']==1:
                # Retain ordinary terminal replies before entering the protocol.
                while b'\x1b[1;16R' not in item['received'] or b'\x1b[?1;2c' not in item['received']:
                    data=await reader.read(4096)
                    if not data:raise ConnectionError('Lost before terminal replies')
                    item['received'].extend(data)
                event('terminal-ready')
                protocol=bytearray()
                if transfer.get('protocol'):
                    from batch_carrier_peer import run as batch_peer
                    await batch_peer(reader,writer,item,event,out,transfer,upload_body)
                elif transfer['upload']:
                    # Genuine receiver negotiation until the real sender starts.
                    while not protocol or protocol[0] not in (1,2):
                        writer.write(b'C');await writer.drain()
                        try:data=await asyncio.wait_for(reader.read(4096),.25)
                        except asyncio.TimeoutError:continue
                        if not data:raise ConnectionError('Lost before upload')
                        item['received'].extend(data);protocol.extend(data)
                        while protocol and protocol[0] not in (1,2):del protocol[0]
                    for number in range(1,3 if transfer['partial'] else 2):
                        while not protocol or protocol[0] not in (1,2):
                            data=await reader.read(4096)
                            if not data:raise ConnectionError('Lost before next frame')
                            item['received'].extend(data);protocol.extend(data)
                        size=128 if protocol[0]==1 else 1024
                        while len(protocol)<size+5:
                            data=await reader.read(4096)
                            if not data:raise ConnectionError('Lost inside frame')
                            item['received'].extend(data);protocol.extend(data)
                        block=bytes(protocol[:size+5]);del protocol[:size+5]
                        offset=(number-1)*size
                        assert block[1:3]==bytes((number,255-number)) and block[3:3+size]==upload_body[offset:offset+size]
                        assert int.from_bytes(block[-2:],'big')==binascii.crc_hqx(block[3:-2],0)
                        event('upload-frame-'+str(number));item.setdefault('frames',[]).append(block.hex())
                        if transfer['partial'] and number==1:
                            writer.write(b'\x06');await writer.drain();event('upload-ACK-1')
                else:
                    while b'C' not in protocol:
                        data=await reader.read(4096)
                        if not data:raise ConnectionError('Lost before download negotiation')
                        item['received'].extend(data);protocol.extend(data)
                    event('download-CRC-request')
                    if transfer['partial']:
                        received_body=bytes(65+i%26 for i in range(11264))
                        for number in range(1,12):
                            body=received_body[(number-1)*1024:number*1024]
                            frame=bytes((2,number,255-number))+body+binascii.crc_hqx(body,0).to_bytes(2,'big')
                            writer.write(frame);await writer.drain();event('download-frame-'+str(number))
                            protocol.clear()
                            while b'\x06' not in protocol:
                                data=await reader.read(4096)
                                if not data:raise ConnectionError('Lost before download ACK')
                                item['received'].extend(data);protocol.extend(data)
                            event('download-ACK-'+str(number))
                        stage_data=(out/'PCRX.$$$').read_bytes()
                        item['stage_before_drop']={'bytes':len(stage_data),'exact':stage_data==received_body[:len(stage_data)]}
                if not transfer.get('fragment'):await asyncio.sleep(.25)
                event('carrier-drop');writer.transport.abort();return
            while data:=await reader.read(4096):
                item['received'].extend(data)
                drop_ready=b'SCRIPTREADY\r' in item['received'] if aspect else b'\x1b[1;16R' in item['received'] and b'\x1b[?1;2c' in item['received']
                if item['index']==1 and drop_ready and not item.get('dropped'):
                    item['dropped']=True
                    await asyncio.sleep(.2)
                    writer.write(b'\x1b[');await writer.drain();event('partial-CSI')
                    await asyncio.sleep(.2);event('carrier-drop');writer.transport.abort();break
                if item['index']==2 and b'ready' in item['received'] and not item.get('keyboard'):
                    item['keyboard']=True;event('keyboard-after-redial')
                    writer.write(b'\x1b[3;1HKEYOK\x1b[6n');await writer.drain()
        except (ConnectionError,OSError,AssertionError) as error:item['errors'].append(repr(error))
        finally:
            writer.close();owners.discard(task);event('closed')
    server=await asyncio.start_server(peer,'127.0.0.1',0);port=server.sockets[0].getsockname()[1]
    target=f'127.0.0.1:{port}'.encode()
    config=bytearray(prm(port=3,baud=5,soft=soft,hard=not soft))
    struct.pack_into('<HH',config,0x4e4,8,4);struct.pack_into('<H',config,0x188,5);struct.pack_into('<H',config,0x1e6,1)
    init=b'AT&K4^M' if soft else b'AT&K3^M';config[0x18:0x47]=init.ljust(47,b'\0')
    directory_bytes=directory(entry=1,target=target,port=3,baud=5)
    (out/'TEST.PRM').write_bytes(config);(out/'TEST.DIR').write_bytes(directory_bytes)
    text=f'''[sdl]
output=surface
[dosbox]
memsize=8
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=modem irq:5 listenport:0
serial4=disabled
[autoexec]
@echo off
mount c "{stage}"
mount d "{out}"
d:
set PCPLUS=
D:\\SNAP B
D:\\SLOWLOG T
D:\\PLWATCH T
ADDKEY {keys}
C:\\TERMINAL @D:\\TEST.PRM /E:D:\\TEST.DIR /N:1{extra_command}
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto capture
:failed
echo FAIL>D:\\FAIL.TXT
:capture
D:\\SNAP S
D:\\PLWATCH
D:\\SLOWLOG
D:\\SNAP A
exit
'''
    (out/'dosbox.conf').write_text(text)
    immutable={str(p):sha(p) for p in [out/'PLWATCH.COM',out/'SLOWLOG.COM',out/'SNAP.COM',out/'dosbox.conf',*aspect_inputs]}
    try:
        with (out/'dosbox.log').open('w') as log:
            process=await asyncio.create_subprocess_exec('dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf'),cwd=out,
                env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log)
            try:code=await asyncio.wait_for(process.wait(),32 if aspect else 28 if transfer else 23)
            except asyncio.TimeoutError:
                process.terminate()
                try:await asyncio.wait_for(process.wait(),3)
                except asyncio.TimeoutError:process.kill();await process.wait()
                code=-1
    finally:
        server.close()
        if hasattr(server,'close_clients'):server.close_clients()
        for task in list(owners):task.cancel()
        await asyncio.gather(*list(owners),return_exceptions=True)
        await asyncio.wait_for(server.wait_closed(),3)
    for item in sessions:
        (out/f"connection-{item['index']}.bin").write_bytes(item.pop('received'))
    captured=(out/'PLSTATE.BIN').read_bytes();assert len(captured)==9798+(18 if aspect else (124 if transfer.get('protocol') else 64) if transfer else 0)
    header=struct.unpack_from('<10H',captured);samples=[captured[20+i*722:20+(i+1)*722] for i in range(header[2])];final=samples[-1]
    logdata=(out/'PCPLUS.FON').read_bytes()
    checks,records=inspect_disk_record(final,2,1,b'LAB NODE 001',target,HEADING+logdata[len(seed):])
    delay=struct.unpack('<26H',(out/'SLOW.BIN').read_bytes())
    before=(out/'BEFORE.BIN').read_bytes();after=(out/'AFTER.BIN').read_bytes();doslog=(out/'dosbox.log').read_text()
    first=(out/'connection-1.bin').read_bytes() if sessions else b'';second=(out/'connection-2.bin').read_bytes() if len(sessions)>1 else b''
    stamp_checks=[]
    for generation,row in enumerate(records,1):
        observed=[r[26:38] for r in samples if struct.unpack_from('<I',r,14)[0]==generation and struct.unpack_from('<H',r,18)[0]==1]
        if generation==1:observed=[struct.pack('<6H',*delay[20:26])]
        try:stamp=dt.datetime.strptime(row['start'][-18:],'%m/%d/%y %H:%M:%S ')
        except ValueError:
            stamp_checks.append(False);continue
        stamp_checks.append(bool(observed) and all(tuple([struct.unpack('<6H',raw)[0]%100,*struct.unpack('<6H',raw)[1:]])==
            (stamp.year%100,stamp.month,stamp.day,stamp.hour,stamp.minute,stamp.second) for raw in observed))
    checks.update(normal_exit=code==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),
        hardware_restored=len(before)==42 and before==after,two_actual_connections=len(sessions)==2,
        actual_first_reply=b'\x1b[1;16R' in first and b'\x1b[?1;2c' in first,
        actual_redial_replies=b'\x1b[1;16R' in second and b'\x1b[?1;2c' in second and b'\x1b[2;10R' in second,
        keyboard_after_redial=b'ready' in second and b'\x1b[3;6R' in second,
        real_modem_loss='Modem response: NO CARRIER' in doslog,
        two_real_initializations=doslog.count('Command sent to modem: ->'+init[:-2].decode()+'<-')==2,
        original_file_prefix=logdata.startswith(seed) and len(logdata)==len(seed)+162,
        exact_file_attempts=struct.unpack_from('<3H',final,716)==(4,0,0),
        observer_final=header[0]==0x4c45 and header[3]==1 and header[9]==0,
        held_real_write=delay[0:3]==(0x534c,1,ticks) and delay[3]>=ticks and delay[10]==64 and not(delay[11]&1),
        DCD_high_at_entry=bool(delay[16]&0x80),actual_loss_during_hold=(delay[18]==1 and not(delay[17]&0x80)) if ticks else delay[18]==0,
        high_DCD_observed=delay[19]==1,IRQs_and_no_RX_loss=bool(delay[4]&0x200) and bool(delay[14]&0x200) and delay[8]==delay[9]==0,
        directory_updated_twice=accounting_check(directory_bytes,(out/'TEST.DIR').read_bytes(),1,2),
        original_START_stamps_preserved=len(stamp_checks)==2 and all(stamp_checks),
        fixture_executables_unchanged=all(sha(Path(p))==h for p,h in immutable.items()),
        PRM_unchanged=(out/'TEST.PRM').read_bytes()==config,peer_errors_absent=all(not s['errors'] for s in sessions))
    aspect_detail={}
    if aspect:
        child=struct.unpack('<9H',captured[9798:]);marker=(out/'CHILD.LOG').read_bytes() if (out/'CHILD.LOG').exists() else b''
        checks.update(actual_ASPECT_progress=b'SCRIPTREADY\r' in first and marker==(b'START|LOST|' if aspect['handler'] else b'START|RETURN|'),
            actual_live_child=child[0]>0 and child[3]==child[4]!=0,
            actual_disconnect_policy=(child[1]>0)==aspect['handler'],
            actual_window_visibility=(child[2]>0)==aspect['window'],
            child_error_free=child[6]==0,child_wait_service=child[7]>0,actual_child_exit=child[8]==1)
        aspect_detail=dict(handler=aspect['handler'],window=aspect['window'],observer=list(child),marker=marker.decode('ascii'),runner_sha256=sha(aspect['runner']))
    transfer_detail={}
    if transfer:
        watch=struct.unpack('<32H',captured[9798:9862]);download=watch[8:18];upload_state=watch[18:32]
        checks.update(actual_transfer=watch[0]>0,carrier_fault=watch[2]==4,transfer_resolved=watch[3:5]==(0,0) and watch[7]==0,
            correct_direction=watch[5]==int(transfer['upload']),no_transfer_RX_drops=watch[6]==0,
            no_download_stage=not (out/'PCRX.$$$').exists() and not (out/'RECV.BIN').exists(),
            receive_handle_closed=download[5:8]==(0,0,0),upload_handle_closed=upload_state[4:8]==(0,0,0,0))
        events=[e['kind'] for e in sessions[0]['events']] if sessions else []
        if transfer.get('protocol'):
            batch_state=struct.unpack('<30H',captured[9862:]);detail=sessions[0].get('batch',{}) if sessions else {}
            expected_files={'FIRST.BIN':b'FIRST COMPLETE FILE\r\n'} if transfer.get('retained') else {}
            checks.update(actual_batch_protocol=batch_state[0]==transfer['protocol'],
                actual_batch_metadata=bool(detail.get('metadata_prefix')) if transfer.get('fragment') else detail.get('metadata',False),
                deliberate_mid_frame_loss=detail.get('metadata_prefix',{}).get('bytes')==16 and not detail.get('metadata',False) if transfer.get('fragment') else 'metadata_prefix' not in detail,
                actual_batch_data=detail.get('data_frames')==(2 if transfer['upload'] else 9) if transfer['partial'] else detail.get('data_frames')==0,
                actual_batch_ACKs=detail.get('ACKed_data_frames')==(1 if transfer['upload'] else 9) if transfer['partial'] else detail.get('ACKed_data_frames')==0,
                exact_receive_tree={p.name:p.read_bytes() for p in (out/'RECV').iterdir()}==expected_files,
                retained_first_file=bool(detail.get('retained_file'))==bool(transfer.get('retained')))
            if transfer['upload']:
                checks.update(batch_upload_aborted=batch_state[15]==4,upload_aborted=upload_state[0]==6,
                    source_unchanged=(out/'SEND.BIN').read_bytes()==upload_body)
            else:
                checks.update(batch_download_aborted=batch_state[1]==4,download_aborted=download[0]==4,
                    exact_received_bytes=(download[8]|download[9]<<16)==(9216 if transfer['partial'] else 0),
                    prior_file_count=(batch_state[13]|batch_state[14]<<16)==int(bool(transfer.get('retained'))))
            transfer['batch_observer']=list(batch_state)
        elif transfer['upload']:
            checks.update(actual_upload_frame='upload-frame-1' in events,
                actual_upload_progress=('upload-ACK-1' in events and 'upload-frame-2' in events) if transfer['partial'] else 'upload-ACK-1' not in events,
                upload_aborted=upload_state[0]==6,source_unchanged=(out/'SEND.BIN').read_bytes()==upload_body)
        else:
            checks.update(actual_download_negotiation='download-CRC-request' in events,
                actual_download_progress=('download-ACK-11' in events)==transfer['partial'],
                real_staged_file=(8192<=sessions[0].get('stage_before_drop',{}).get('bytes',0)<=10240 and sessions[0]['stage_before_drop']['exact']) if transfer['partial'] else 'stage_before_drop' not in sessions[0],
                download_aborted=download[0]==4,exact_received_bytes=(download[8]|download[9]<<16)==(10240 if transfer['partial'] else 0))
        transfer_detail=dict(transfer,observer=list(watch))
    result=dict(case=name,passed=all(checks.values()),checks=checks,records=records,slow_snapshot=list(delay),observer_header=list(header),sessions=sessions,aspect=aspect_detail,transfer=transfer_detail,
        artifacts={str(p.relative_to(ROOT)):sha(p) for p in out.rglob('*') if p.is_file()})
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(name,'PASS' if result['passed'] else json.dumps({k:v for k,v in checks.items() if not v}),flush=True)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--label',required=True)
    p.add_argument('--fragment',action='store_true');p.add_argument('--batch',action='store_true');p.add_argument('--transfer',action='store_true');p.add_argument('--aspect',action='store_true');p.add_argument('--runner',type=Path)
    p.add_argument('--case',choices=['idle-hard','write-hard','write-soft','aspect-wait','aspect-when','aspect-wait-window','aspect-when-window','receive-negotiation','receive-partial','upload-unacked','upload-partial',*[f'{protocol}-{kind}' for protocol in ('ymodem','zmodem') for kind in ('receive-metadata','receive-partial','receive-retained','upload-metadata','upload-partial')],*[f'{protocol}-fragment-{policy}' for protocol in ('ymodem','zmodem') for policy in ('legacy','strict')]]);a=p.parse_args();assert sum((a.aspect,a.transfer,a.batch,a.fragment))<=1;assert re.fullmatch('[a-z0-9-]+',a.label)
    parent=a.terminal.resolve();manifest=json.loads((parent/'manifest.json').read_text());assert manifest['experimental_phone_log_controls']
    original=sha(parent/'TERMINAL.EXE');assert original==manifest['binary_sha256']
    out=ROOT/'build/phone-log-carrier-terminal'/a.label;assert not out.exists();out.mkdir(parents=True)
    sources=dict(manifest['sources'])
    runner=None
    if a.aspect:
        assert a.runner
        from product_inputs import select_product
        runner,child_sources=select_product(a.runner,'ASPECT.EXE')
        for source in child_sources:
            if source.is_relative_to(ROOT/'build'):continue
            relative=source.relative_to(ROOT).as_posix();digest=sha(source)
            assert relative not in sources or sources[relative]==digest
            sources[relative]=digest
        sources['standalone/test_directory_key_bindings_dos.py']=sha(ROOT/'standalone/test_directory_key_bindings_dos.py')
        sources['src/aspect/compiler.py']=sha(ROOT/'src/aspect/compiler.py')
    for n in ['standalone/test_phone_log_carrier_terminal.py','standalone/phone_log_slow_write.asm','standalone/test_phone_log_events_terminal.py',
              'standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py',
              'standalone/test_terminal.py','standalone/phone_log_events_watch.asm','lab/bbs/phone_log_evidence.py','lab/bbs/product_inputs.py']:
        sources[n]=sha(ROOT/n)
    if a.batch or a.fragment:
        for n in ('standalone/batch_carrier_peer.py','standalone/check_zmodem_wire.py'):sources[n]=sha(ROOT/n)
    rows=[]
    cases=[('idle-hard',0,0),('write-hard',36,0),('write-soft',36,1)]
    if a.aspect:cases=[(name,0,0) for name in ('aspect-wait','aspect-when','aspect-wait-window','aspect-when-window')]
    if a.transfer:cases=[(name,0,0) for name in ('receive-negotiation','receive-partial','upload-unacked','upload-partial')]
    if a.batch:cases=[(f'{protocol}-{kind}',0,0) for protocol in ('ymodem','zmodem') for kind in ('receive-metadata','receive-partial','receive-retained','upload-metadata','upload-partial')]
    if a.fragment:cases=[(f'{protocol}-fragment-{policy}',0,0) for protocol in ('ymodem','zmodem') for policy in ('legacy','strict')]
    assert not a.case or any(row[0]==a.case for row in cases)
    for name,ticks,soft in cases:
        if a.case and a.case!=name:continue
        aspect=dict(runner=runner,handler='when' in name,window=name.endswith('window')) if a.aspect else None
        transfer=dict(upload=name.startswith('upload'),partial=name.endswith('partial')) if a.transfer else None
        if a.batch:transfer=dict(protocol=1 if name.startswith('ymodem') else 2,upload='upload' in name,partial=name.endswith(('partial','retained')),retained=name.endswith('retained'))
        if a.fragment:transfer=dict(protocol=1 if name.startswith('ymodem') else 2,upload=True,partial=False,retained=False,fragment=True,strict=name.endswith('strict'))
        rows.append(asyncio.run(run_case(parent,out/name,name,ticks,soft,aspect,transfer)))
    checks=dict(all_cases=bool(rows) and all(r['passed'] for r in rows),sources_unchanged=all(sha(ROOT/n)==h for n,h in sources.items()),binary_unchanged=sha(parent/'TERMINAL.EXE')==original)
    result=dict(passed=all(checks.values()),checks=checks,cases=rows,sources=sources,
        artifacts={p:h for row in rows for p,h in row['artifacts'].items()},terminal_sha256=original,original_inputs=[],aspect_matrix=a.aspect,transfer_matrix=a.transfer,batch_matrix=a.batch,fragment_matrix=a.fragment,
        scope=__doc__+' Built-in DOSBox modem generates CONNECT/NO CARRIER and actual virtual DCD. Peer only sends ANSI/protocol bytes and closes TCP; no injected modem replies or product variables. MSR reads clear delta bits; native policy uses carrier level. Not physical carrier/SIP/analog or all child/transfer acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(checks));assert result['passed']

if __name__=='__main__':main()
