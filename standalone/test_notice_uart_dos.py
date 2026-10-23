#!/usr/bin/env python3
"""Actual notice popup retains independent peer bytes across UART/flow policies."""
import argparse,hashlib,itertools,json,os,re,shutil,socket,subprocess,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PAYLOAD=bytes(value for value in range(256) if value not in (17,19))*2
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--banked',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/('build/notice-bank-uart' if a.banked else 'build/notice-uart');m=json.loads((base/'manifest.json').read_text());assert m['original_inputs']==[]
    assert sha(base/'NUART.EXE')==m['binary_sha256'] and all(sha(ROOT/path)==h for path,h in m['sources'].items())
    cases=[]
    for port,flow,mode in itertools.product([1,2],'NSHB','NE'):
        folder=out/f'com{port}-{flow}-{mode}';folder.mkdir();shutil.copy2(base/'NUART.EXE',folder/'NUART.EXE')
        server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(.2);stop=threading.Event();done=threading.Event();wire=bytearray();events=[];errors=[];started=time.monotonic()
        def peer():
            try:
                connection=None
                while not stop.is_set():
                    try:connection,_=server.accept();break
                    except socket.timeout:continue
                if connection is None:return
                stage=0
                with connection:
                    connection.settimeout(.1)
                    while not stop.is_set():
                        try:data=connection.recv(4096)
                        except socket.timeout:continue
                        if not data:events.append(dict(kind='EOF',seconds=time.monotonic()-started));break
                        wire.extend(data);events.append(dict(kind='receive',hex=data.hex(),seconds=time.monotonic()-started))
                        if b'R' in wire and not stage:
                            packet=(b'\x13'+PAYLOAD+b'\x11') if flow in 'SB' else PAYLOAD
                            connection.sendall(packet);events.append(dict(kind='send-completed',hex=packet.hex(),seconds=time.monotonic()-started));stage=1
                        if b'P' in wire and stage==1:
                            connection.sendall(b'READY!');events.append(dict(kind='send-completed',hex=b'READY!'.hex(),seconds=time.monotonic()-started));stage=2
            except OSError as error:
                if not stop.is_set():errors.append(str(error))
            finally:done.set()
        thread=threading.Thread(target=peer,daemon=True);thread.start()
        serial=[f'serial{i}=disabled' for i in range(1,5)];serial[port-1]=f'serial{port}=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1'
        cfg=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
{chr(10).join(serial)}
[autoexec]
@echo off
mount c "{folder}"
c:
NUART /S{port}:0003:03:{flow} {mode} >OUTPUT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
exit
:failed
echo FAIL>FAIL.TXT
exit
'''
        (folder/'dosbox.conf').write_text(cfg);code=None
        try:
            with (folder/'dosbox.log').open('w') as log:process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=25);code=process.returncode
            done.wait(2)
        finally:stop.set();server.close();thread.join(1)
        (folder/'peer.json').write_text(json.dumps(dict(events=events,errors=errors),indent=2)+'\n');(folder/'wire.bin').write_bytes(wire)
        text=(folder/'OUTPUT.TXT').read_text() if (folder/'OUTPUT.TXT').exists() else '';match=re.fullmatch(r'NOTICE UART COM(\d) ([NSHB]) ([NE]) (\d+) checks (\d+) callbacks (\d+) maximum\s*',text)
        checks=dict(emulator_exit=code==0,DOS_exit=(folder/'PASS.TXT').exists() and not(folder/'FAIL.TXT').exists(),actual_checks=bool(match) and int(match[6])==508 and int(match[5])>1,raw_retained=(folder/'RX.BIN').exists() and (folder/'RX.BIN').read_bytes()==PAYLOAD,wire_exact=bytes(wire)==(b'\x11RPF\x13' if flow in 'SB' else b'RPF'),peer_clean=not errors and any(e['kind']=='EOF' for e in events),binary_unchanged=sha(folder/'NUART.EXE')==m['binary_sha256'])
        row=dict(port=port,flow=flow,mode=mode,passed=all(checks.values()),checks=checks,assertions=int(match[4]) if match else None,callbacks=int(match[5]) if match else None,maximum=int(match[6]) if match else None,folder=str(folder.relative_to(ROOT)),captures_sha256={path.name:sha(path) for path in folder.iterdir() if path.is_file()})
        cases.append(row);print(json.dumps(dict(port=port,flow=flow,mode=mode,passed=row['passed'],checks=checks,output=text)),flush=True)
        (out/'result.json').write_text(json.dumps(dict(passed=len(cases)==16 and all(r['passed'] for r in cases),cases=cases,binary_sha256=m['binary_sha256'],inputs={**m['sources'],str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str((base/'manifest.json').relative_to(ROOT)):sha(base/'manifest.json')},payload_hex=PAYLOAD.hex(),scope=__doc__+' Sixteen actual8086 DOS COM1/COM2 N/S/H/B cases crossed with native timed completion or injected service error. Real UART ISR/flow/queue and window cleanup;508 exact bytes received during the popup, retained until afterward, followed by READY! interaction and UART/vector/PIC restoration. Local raw peer, no Telnet/BBS/physical timing. Nullmodem CTS stays ready and does not enforce RTS; software XOFF/XON are explicit peer stimuli; guest software-flow startup XON and shutdown XOFF must match exactly.'),indent=2)+'\n')
        if not row['passed']:raise AssertionError('Preserve failed UART notice cohort')
if __name__=='__main__':main()
