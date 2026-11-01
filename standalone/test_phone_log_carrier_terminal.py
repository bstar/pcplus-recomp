#!/usr/bin/env python3
"""Real emulated DCD loss and same-parent redial with checked call logging."""
import argparse,asyncio,datetime as dt,json,os,re,struct,subprocess,sys,time
from pathlib import Path
from build_phone_log_queue import ROOT,sha
from directory_fixtures import directory,prm
from directory_test_support import accounting_check
from test_terminal import SAMPLER
from test_phone_log_events_terminal import HEADING,OLD_CALL,inspect_disk_record
sys.path.insert(0,str(ROOT/'lab/bbs'))
from phone_log_evidence import build_observer


async def run_case(parent,out,name,ticks,soft):
    out.mkdir(parents=True);binary=parent/'TERMINAL.EXE'
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(parent/'terminal.map').read_text(),re.M|re.I)}
    observer=build_observer(binary,out/'PLWATCH.COM',irq=5)
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
            while data:=await reader.read(4096):
                item['received'].extend(data)
                if item['index']==1 and b'\x1b[1;16R' in item['received'] and b'\x1b[?1;2c' in item['received'] and not item.get('dropped'):
                    item['dropped']=True
                    await asyncio.sleep(.2)
                    writer.write(b'\x1b[');await writer.drain();event('partial-CSI')
                    await asyncio.sleep(.2);event('carrier-drop');writer.transport.abort();break
                if item['index']==2 and b'ready' in item['received'] and not item.get('keyboard'):
                    item['keyboard']=True;event('keyboard-after-redial')
                    writer.write(b'\x1b[3;1HKEYOK\x1b[6n');await writer.drain()
        except (ConnectionError,OSError) as error:item['errors'].append(type(error).__name__)
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
mount c "{parent}"
mount d "{out}"
d:
set PCPLUS=
D:\\SNAP B
D:\\SLOWLOG T
D:\\PLWATCH T
ADDKEY p900 enter p6000 a-d p4500 r e a d y p1800 a-x
C:\\TERMINAL @D:\\TEST.PRM /E:D:\\TEST.DIR /N:1
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
    immutable={str(p):sha(p) for p in (out/'PLWATCH.COM',out/'SLOWLOG.COM',out/'SNAP.COM',out/'dosbox.conf')}
    try:
        with (out/'dosbox.log').open('w') as log:
            process=await asyncio.create_subprocess_exec('dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf'),cwd=out,
                env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log)
            try:code=await asyncio.wait_for(process.wait(),23)
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
    captured=(out/'PLSTATE.BIN').read_bytes();assert len(captured)==9798
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
        stamp=dt.datetime.strptime(row['start'][-18:],'%m/%d/%y %H:%M:%S ')
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
    result=dict(case=name,passed=all(checks.values()),checks=checks,records=records,slow_snapshot=list(delay),observer_header=list(header),sessions=sessions,
        artifacts={str(p.relative_to(ROOT)):sha(p) for p in out.rglob('*') if p.is_file()})
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(name,'PASS' if result['passed'] else json.dumps({k:v for k,v in checks.items() if not v}),flush=True)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--label',required=True)
    p.add_argument('--case',choices=['idle-hard','write-hard','write-soft']);a=p.parse_args();assert re.fullmatch('[a-z0-9-]+',a.label)
    parent=a.terminal.resolve();manifest=json.loads((parent/'manifest.json').read_text());assert manifest['experimental_phone_log_controls']
    original=sha(parent/'TERMINAL.EXE');assert original==manifest['binary_sha256']
    out=ROOT/'build/phone-log-carrier-terminal'/a.label;assert not out.exists();out.mkdir(parents=True)
    sources=dict(manifest['sources'])
    for n in ['standalone/test_phone_log_carrier_terminal.py','standalone/phone_log_slow_write.asm','standalone/test_phone_log_events_terminal.py',
              'standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py',
              'standalone/test_terminal.py','standalone/phone_log_events_watch.asm','lab/bbs/phone_log_evidence.py','lab/bbs/product_inputs.py']:
        sources[n]=sha(ROOT/n)
    rows=[]
    for name,ticks,soft in [('idle-hard',0,0),('write-hard',36,0),('write-soft',36,1)]:
        if a.case and a.case!=name:continue
        rows.append(asyncio.run(run_case(parent,out/name,name,ticks,soft)))
    checks=dict(all_cases=bool(rows) and all(r['passed'] for r in rows),sources_unchanged=all(sha(ROOT/n)==h for n,h in sources.items()),binary_unchanged=sha(parent/'TERMINAL.EXE')==original)
    result=dict(passed=all(checks.values()),checks=checks,cases=rows,sources=sources,
        artifacts={p:h for row in rows for p,h in row['artifacts'].items()},terminal_sha256=original,original_inputs=[],
        scope=__doc__+' Built-in DOSBox modem generates CONNECT/NO CARRIER and actual virtual DCD. Peer only sends ANSI and closes TCP; no injected modem replies or product variables. MSR reads clear delta bits; native policy uses carrier level. Not physical carrier/SIP/analog or all child/transfer acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(checks));assert result['passed']

if __name__=='__main__':main()
